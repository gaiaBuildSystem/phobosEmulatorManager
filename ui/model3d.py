import json
import math
import struct
import threading
import numpy as np

# Small software renderer for static .glb models
# Slint does not have a 3D element, so we rasterize the model with numpy
# and hand the frames over to a Slint Image

_COMPONENT_DTYPES = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32
}

_TYPE_SIZES = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT4": 16
}


def _quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2*(y*y + z*z), 2*(x*y - z*w), 2*(x*z + y*w)],
        [2*(x*y + z*w), 1 - 2*(x*x + z*z), 2*(y*z - x*w)],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x*x + y*y)]
    ])


def _node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T

    mat = np.eye(4)
    rot = _quat_to_mat(node.get("rotation", [0, 0, 0, 1]))
    scale = np.diag(node.get("scale", [1, 1, 1]))
    mat[:3, :3] = rot @ scale
    mat[:3, 3] = node.get("translation", [0, 0, 0])
    return mat


class GlbModel:
    """
    Loads the triangles of a .glb file flattened in world space
    with the base color of the material of each triangle
    """

    def __init__(self, path: str):
        with open(path, "rb") as f:
            data = f.read()

        magic, _, _ = struct.unpack("<4sII", data[:12])
        if magic != b"glTF":
            raise ValueError(f"{path} is not a glb file")

        json_len = struct.unpack("<I", data[12:16])[0]
        self.__gltf = json.loads(data[20:20 + json_len])
        bin_start = 20 + json_len + 8
        self.__bin = data[bin_start:]

        self.__vertices = []
        self.__normals = []
        self.__colors = []

        scene = self.__gltf["scenes"][self.__gltf.get("scene", 0)]
        for node_index in scene["nodes"]:
            self.__walk(node_index, np.eye(4))

        # vertices: (N, 3, 3) | normals: (N, 3, 3) | colors: (N, 3)
        self.vertices = np.concatenate(self.__vertices)
        self.normals = np.concatenate(self.__normals)
        self.colors = np.concatenate(self.__colors)

        # center the model on the origin
        vmin = self.vertices.reshape(-1, 3).min(axis=0)
        vmax = self.vertices.reshape(-1, 3).max(axis=0)
        self.vertices -= (vmin + vmax) / 2

        # perspective camera distance, relative to the model size
        self.camera = 3.0 * float(np.linalg.norm(vmax - vmin) / 2)
        self.half_extents = (1.0, 1.0)
        self.fit_angles(0.0, 0.0)


    @staticmethod
    def rotation(yaw: float, pitch: float) -> np.ndarray:
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        rot_x = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
        return rot_x @ rot_y


    def __project(self, verts):
        persp = self.camera / (self.camera - verts[..., 2])
        return verts[..., 0] * persp, verts[..., 1] * persp


    def fit_angles(self, max_yaw: float, max_pitch: float):
        """
        Fits the framing so the model never leaves the frame
        while rotating inside the given yaw/pitch ranges (radians)
        """
        flat = self.vertices.reshape(-1, 3)
        half_x, half_y = 0.0, 0.0
        for yaw in (-max_yaw, 0.0, max_yaw):
            for pitch in (-max_pitch, 0.0, max_pitch):
                x, y = self.__project(flat @ self.rotation(yaw, pitch).T)
                half_x = max(half_x, float(np.abs(x).max()))
                half_y = max(half_y, float(np.abs(y).max()))
        self.half_extents = (half_x, half_y)


    def __accessor(self, index):
        accessor = self.__gltf["accessors"][index]
        view = self.__gltf["bufferViews"][accessor["bufferView"]]
        dtype = _COMPONENT_DTYPES[accessor["componentType"]]
        size = _TYPE_SIZES[accessor["type"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        count = accessor["count"]
        stride = view.get("byteStride", 0)
        itemsize = np.dtype(dtype).itemsize * size

        if stride and stride != itemsize:
            raw = np.frombuffer(self.__bin, dtype=np.uint8, count=stride * count, offset=offset)
            raw = raw.reshape(count, stride)[:, :itemsize].copy()
            return raw.view(dtype).reshape(count, size)

        arr = np.frombuffer(self.__bin, dtype=dtype, count=count * size, offset=offset)
        return arr.reshape(count, size) if size > 1 else arr


    def __walk(self, node_index, parent):
        node = self.__gltf["nodes"][node_index]
        world = parent @ _node_matrix(node)

        if "mesh" in node:
            normal_mat = np.linalg.inv(world[:3, :3]).T
            for prim in self.__gltf["meshes"][node["mesh"]]["primitives"]:
                # only triangles
                if prim.get("mode", 4) != 4:
                    continue

                pos = self.__accessor(prim["attributes"]["POSITION"]).astype(np.float64)
                pos = pos @ world[:3, :3].T + world[:3, 3]

                if "NORMAL" in prim["attributes"]:
                    nrm = self.__accessor(prim["attributes"]["NORMAL"]).astype(np.float64)
                    nrm = nrm @ normal_mat.T
                    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
                else:
                    nrm = None

                if "indices" in prim:
                    idx = self.__accessor(prim["indices"]).astype(np.int64).reshape(-1, 3)
                else:
                    idx = np.arange(len(pos)).reshape(-1, 3)

                tris = pos[idx]
                if nrm is None:
                    face = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
                    face /= np.linalg.norm(face, axis=1, keepdims=True) + 1e-12
                    tri_nrm = np.repeat(face[:, None, :], 3, axis=1)
                else:
                    tri_nrm = nrm[idx]

                color = [0.8, 0.8, 0.8]
                if "material" in prim:
                    material = self.__gltf["materials"][prim["material"]]
                    color = material.get("pbrMetallicRoughness", {}).get(
                        "baseColorFactor", [0.8, 0.8, 0.8, 1]
                    )[:3]

                self.__vertices.append(tris)
                self.__normals.append(tri_nrm)
                self.__colors.append(np.tile(color, (len(tris), 1)))

        for child in node.get("children", []):
            self.__walk(child, world)


    def render(self, width: int, height: int, yaw: float, pitch: float = 0.0, supersample: int = 2) -> np.ndarray:
        """
        Renders the model rotated by yaw/pitch (radians) and returns
        an RGBA uint8 array with transparent background
        """
        sw, sh = width * supersample, height * supersample

        rot = self.rotation(yaw, pitch)
        verts = self.vertices @ rot.T
        nrms = self.normals @ rot.T

        # perspective projection, y down for the image
        scale = min(sw / 2 / self.half_extents[0], sh / 2 / self.half_extents[1]) * 0.95
        proj_x, proj_y = self.__project(verts)
        px = proj_x * scale + sw / 2
        py = -proj_y * scale + sh / 2
        pz = verts[..., 2]

        # lighting per vertex (gouraud), materials are double sided
        light = np.array([-0.4, 0.5, 0.75])
        light /= np.linalg.norm(light)
        view = np.array([0.0, 0.0, 1.0])
        half = light + view
        half /= np.linalg.norm(half)

        nrms = np.where((nrms[..., 2:3] < 0), -nrms, nrms)
        diffuse = np.clip(nrms @ light, 0, 1)
        specular = np.clip(nrms @ half, 0, 1) ** 40 * 0.35
        # base colors are linear, convert to sRGB
        base = self.colors[:, None, :] ** (1 / 2.2)
        shade = base * (0.55 + 0.8 * diffuse[..., None]) + specular[..., None]

        # bounding box of each triangle
        x0 = np.clip(np.floor(px.min(axis=1)), 0, sw - 1).astype(np.int64)
        x1 = np.clip(np.ceil(px.max(axis=1)), 0, sw - 1).astype(np.int64)
        y0 = np.clip(np.floor(py.min(axis=1)), 0, sh - 1).astype(np.int64)
        y1 = np.clip(np.ceil(py.max(axis=1)), 0, sh - 1).astype(np.int64)
        bw = x1 - x0 + 1
        bh = y1 - y0 + 1

        area = (px[:, 1] - px[:, 0]) * (py[:, 2] - py[:, 0]) - (px[:, 2] - px[:, 0]) * (py[:, 1] - py[:, 0])
        valid = np.abs(area) > 1e-9

        # expand every triangle into the candidate pixels of its bounding box
        counts = np.where(valid, bw * bh, 0)
        tri = np.repeat(np.arange(len(counts)), counts)
        local = np.arange(counts.sum()) - np.repeat(np.cumsum(counts) - counts, counts)
        pix_x = x0[tri] + local % bw[tri]
        pix_y = y0[tri] + local // bw[tri]
        cx = pix_x + 0.5
        cyy = pix_y + 0.5

        # barycentric coordinates
        ax, ay = px[tri, 0], py[tri, 0]
        bx, by = px[tri, 1], py[tri, 1]
        qx, qy = px[tri, 2], py[tri, 2]
        inv_area = 1.0 / area[tri]
        w1 = ((cx - ax) * (qy - ay) - (qx - ax) * (cyy - ay)) * inv_area
        w2 = ((bx - ax) * (cyy - ay) - (cx - ax) * (by - ay)) * inv_area
        w0 = 1 - w1 - w2
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)

        tri, pix_x, pix_y = tri[inside], pix_x[inside], pix_y[inside]
        w0, w1, w2 = w0[inside, None], w1[inside, None], w2[inside, None]
        depth = (w0[:, 0] * pz[tri, 0] + w1[:, 0] * pz[tri, 1] + w2[:, 0] * pz[tri, 2])
        color = w0 * shade[tri, 0] + w1 * shade[tri, 1] + w2 * shade[tri, 2]

        # z-buffer: sort by depth so the nearest fragment is written last
        order = np.argsort(depth, kind="stable")
        flat = pix_y[order] * sw + pix_x[order]
        rgba = np.zeros((sh * sw, 4), dtype=np.float64)
        rgba[flat, :3] = color[order]
        rgba[flat, 3] = 1.0

        # downsample for antialiasing
        rgba = rgba.reshape(height, supersample, width, supersample, 4).mean(axis=(1, 3))
        # premultiplied average -> straight alpha
        alpha = rgba[..., 3:4]
        rgb = np.where(alpha > 0, rgba[..., :3] / np.maximum(alpha, 1e-9), 0)
        out = np.concatenate([np.clip(rgb, 0, 1), alpha], axis=-1)

        return (out * 255 + 0.5).astype(np.uint8)


_VERTEX_SHADER = """
#version 330
uniform mat3 rotation;
uniform float camera;
uniform vec2 scale;

in vec3 in_position;
in vec3 in_normal;
in vec3 in_color;

out vec3 v_normal;
out vec3 v_color;

void main() {
    vec3 pos = rotation * in_position;
    float persp = camera / (camera - pos.z);
    gl_Position = vec4(pos.xy * persp * scale, -pos.z / camera, 1.0);
    v_normal = rotation * in_normal;
    v_color = in_color;
}
"""

_FRAGMENT_SHADER = """
#version 330
in vec3 v_normal;
in vec3 v_color;
out vec4 f_color;

void main() {
    vec3 light = normalize(vec3(-0.4, 0.5, 0.75));
    vec3 half_dir = normalize(light + vec3(0.0, 0.0, 1.0));
    // materials are double sided
    vec3 n = normalize(v_normal);
    if (n.z < 0.0) {
        n = -n;
    }
    float diffuse = clamp(dot(n, light), 0.0, 1.0);
    float specular = pow(clamp(dot(n, half_dir), 0.0, 1.0), 40.0) * 0.35;
    // base colors are linear, convert to sRGB
    vec3 base = pow(v_color, vec3(1.0 / 2.2));
    f_color = vec4(clamp(base * (0.55 + 0.8 * diffuse) + specular, 0.0, 1.0), 1.0);
}
"""


class GlRenderer:
    """
    Renders a GlbModel with an offscreen OpenGL context
    fast enough to render every frame at the exact rotation
    """

    def __init__(self, model: GlbModel, width: int, height: int, samples: int = 4):
        # imported here so the software renderer works without moderngl
        import moderngl

        self.width = width
        self.height = height
        self.__model = model
        # egl so it does not touch the GLX context used by Slint in the same X connection
        self.__ctx = moderngl.create_standalone_context(backend="egl")

        self.__program = self.__ctx.program(
            vertex_shader=_VERTEX_SHADER,
            fragment_shader=_FRAGMENT_SHADER
        )

        colors = np.repeat(model.colors[:, None, :], 3, axis=1)
        data = np.concatenate([
            model.vertices.reshape(-1, 3),
            model.normals.reshape(-1, 3),
            colors.reshape(-1, 3)
        ], axis=1).astype("f4")
        self.__vbo = self.__ctx.buffer(data.tobytes())
        self.__vao = self.__ctx.vertex_array(
            self.__program,
            [(self.__vbo, "3f 3f 3f", "in_position", "in_normal", "in_color")]
        )

        # multisampled target for antialiasing, resolved into a plain one to read back
        self.__msaa = self.__ctx.framebuffer(
            color_attachments=[self.__ctx.renderbuffer((width, height), 4, samples=samples)],
            depth_attachment=self.__ctx.depth_renderbuffer((width, height), samples=samples)
        )
        self.__resolve = self.__ctx.framebuffer(
            color_attachments=[self.__ctx.renderbuffer((width, height), 4)]
        )

        scale = min(width / 2 / model.half_extents[0], height / 2 / model.half_extents[1]) * 0.95
        self.__program["scale"].value = (scale / (width / 2), scale / (height / 2))
        self.__program["camera"].value = model.camera


    def render(self, yaw: float, pitch: float = 0.0) -> np.ndarray:
        """
        Renders the model rotated by yaw/pitch (radians) and returns
        an RGBA uint8 array with transparent background
        """
        import moderngl

        # numpy is row major, glsl expects column major
        rot = GlbModel.rotation(yaw, pitch)
        self.__program["rotation"].write(rot.T.astype("f4").tobytes())

        self.__msaa.use()
        self.__ctx.enable(moderngl.DEPTH_TEST)
        self.__ctx.clear(0.0, 0.0, 0.0, 0.0)
        self.__vao.render(moderngl.TRIANGLES)
        self.__ctx.copy_framebuffer(self.__resolve, self.__msaa)

        raw = self.__resolve.read(components=4)
        rgba = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 4)[::-1]

        # the resolved edges are premultiplied, Slint wants straight alpha
        alpha = rgba[..., 3:4].astype(np.uint16)
        out = rgba.copy()
        edge = (alpha > 0) & (alpha < 255)
        out[..., :3] = np.where(
            edge,
            np.minimum(rgba[..., :3].astype(np.uint16) * 255 // np.maximum(alpha, 1), 255),
            rgba[..., :3]
        ).astype(np.uint8)
        return out


class GlRenderThread:
    """
    Owns a GlRenderer in its own thread, so its GL context never
    interferes with the one used by the UI thread
    """

    def __init__(self, model: GlbModel, width: int, height: int):
        self.__cond = threading.Condition()
        self.__request = None
        self.__frame = None
        self.__ready = threading.Event()
        self.__error: Exception | None = None

        threading.Thread(
            target=self.__run, args=(model, width, height), daemon=True
        ).start()

        # wait the context creation so failures are reported to the caller
        self.__ready.wait()
        if self.__error is not None:
            raise self.__error


    def __run(self, model, width, height):
        try:
            renderer = GlRenderer(model, width, height)
        except Exception as e:
            self.__error = e
            self.__ready.set()
            return

        self.__ready.set()
        while True:
            with self.__cond:
                while self.__request is None:
                    self.__cond.wait()
                yaw, pitch = self.__request
                self.__request = None

            frame = renderer.render(yaw, pitch)
            with self.__cond:
                self.__frame = frame


    def request(self, yaw: float, pitch: float):
        """Asks for a new frame, replacing any request not started yet"""
        with self.__cond:
            self.__request = (yaw, pitch)
            self.__cond.notify()


    def take_frame(self) -> np.ndarray | None:
        """Returns the last rendered frame, or None if there is no new one"""
        with self.__cond:
            frame, self.__frame = self.__frame, None
        return frame
