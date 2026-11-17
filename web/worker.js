const runtimeUrl = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";
const modules = [
  "DXF_to_lapdata", "cone_to_ini", "lapdata_to_xy",
  "track_characterization", "track_pipeline", "bridge",
];

let runtime;

async function initialize() {
  importScripts(runtimeUrl + "pyodide.js");
  const py = await loadPyodide({ indexURL: runtimeUrl });
  py.FS.mkdir("/app");
  py.FS.mkdir("/input");
  await Promise.all([
    (async () => {
      await py.loadPackage(["micropip", "matplotlib"]);
      const micropip = py.pyimport("micropip");
      try {
        await micropip.install(["ezdxf==1.4.4", "openpyxl==3.1.5"]);
      } finally {
        micropip.destroy();
      }
    })(),
    ...modules.map(async (name) => {
      const response = await fetch(name === "bridge" ? "./bridge.py" : "./python/" + name + ".py");
<<<<<<< HEAD
      if (!response.ok) throw new Error(`Could not load the ${name} module.`);
=======
      if (!response.ok) throw new Error("無法讀取程式檔 " + name);
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39
      py.FS.writeFile("/app/" + name + ".py", new Uint8Array(await response.arrayBuffer()));
    }),
  ]);
  py.runPython("import sys; sys.path.insert(0, '/app'); from bridge import dispatch");
  return { py, dispatch: py.globals.get("dispatch") };
}

self.onmessage = async ({ data: { id, operation, args, bytes, bundled } }) => {
  try {
    runtime ??= initialize().catch((error) => {
      runtime = undefined;
<<<<<<< HEAD
      throw new Error("Could not load the processing engine. Check your internet connection and try again.", { cause: error });
=======
      throw new Error("無法載入瀏覽器運算工具。請確認網路連線後重試。", { cause: error });
>>>>>>> 62778b8eb98f41e0b8dcc8191be6eacc9d45ca39
    });
    const { py, dispatch } = await runtime;
    let path;
    try {
      if (operation === "load") {
        path = bundled ? "/app/fsae_A_2025.dxf" : "/input/drawing.dxf";
        py.FS.writeFile(path, new Uint8Array(bytes));
        args.path = path;
      }
      self.postMessage({ id, result: JSON.parse(dispatch(operation, JSON.stringify(args))) });
    } finally {
      if (path) py.FS.unlink(path);
    }
  } catch (error) {
    const message = error.message.trim().split("\n").pop().replace(/^[\w.]+(?:Error|Exception):\s*/, "");
    self.postMessage({ id, error: message });
  }
};
