const el = (id) => document.getElementById(id);
const dxf = el("dxf");
const map = el("map");
const startInput = el("start");
const routeLayer = el("route-layer");
const circleLayer = el("circle-layer");
const xyMode = el("xy-mode");
const xyValue = el("xy-value");
const titles = ["Track Order", "Choose Start", "Driving Direction", "Analysis and Export"];
const nextLabels = ["Choose Start", "Confirm Start", "Confirm Direction", "Run Analysis"];
const viewControls = ["zoom-out", "zoom-in", "zoom-reset"];
const editing = [...document.querySelectorAll(".panel input, .panel select, .ini-settings")];
const exportButtons = [...document.querySelectorAll("[data-export]")];
const navButtons = ["route-tab", "circle-tab", "route-sample", "circle-sample", "back", "apply-tolerance"];
const worker = new Worker(new URL("./worker.js", import.meta.url));
const requests = new Map();
let nextRequest = 0;
let drawing = null;
let route = [];
let ordered = [];
let points = [];
let step = 0;
let mode = "route";
let view = "map";
let analysis = null;
let analysisUrl;
let busy = false;
let routeNote = "";
let circleNote = "";
let appliedTolerance;
const xyOptions = { distance: 1, segment: 5 };
let iniOptions = {
  model_offset: 0, height: -0.419, model_file: "cone.kn5", name: "AC_POBJECT_999_3",
  rotation: [0, 0, 0], physical: true,
};

worker.addEventListener("message", ({ data: { id, result, error } }) => {
  const pending = requests.get(id);
  if (!pending) return;
  requests.delete(id);
  if (error !== undefined) pending.reject(new Error(error));
  else pending.resolve(result);
});
worker.addEventListener("error", () => {
  for (const pending of requests.values()) pending.reject(new Error("The processing engine stopped responding. Reload the page and try again."));
  requests.clear();
});

function request(operation, args, bytes, bundled = false) {
  return new Promise((resolve, reject) => {
    const id = ++nextRequest;
    requests.set(id, { resolve, reject });
    worker.postMessage({ id, operation, args, bytes, bundled }, bytes ? [bytes] : []);
  });
}

function status(message, error = false) {
  el("status").textContent = message;
  el("status").dataset.error = String(error);
}

async function perform(task) {
  if (busy) return;
  busy = true;
  render();
  try {
    await task();
  } catch (error) {
    status(error.message, true);
  } finally {
    busy = false;
    render();
  }
}

function positive(input, label) {
  const value = input.valueAsNumber;
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${label} must be a number greater than zero.`);
  return value;
}

function startIndex() {
  const number = startInput.valueAsNumber;
  return Number.isInteger(number) && number > 0 && number <= route.length ? number : null;
}

function direction() {
  return document.querySelector("[name='direction']:checked").value === "reverse";
}

function selectedLayer(select) {
  return select.selectedIndex === 0 ? null : select.value;
}

function populateLayers(select, layers, preferred) {
  const choices = [new Option("All layers", ""), ...layers.map((layer) => new Option(layer, layer))];
  select.replaceChildren(...choices);
  if (preferred) select.value = preferred;
}

function clearAnalysis() {
  analysis = null;
  view = "map";
  if (analysisUrl) {
    el("analysis-plot").removeAttribute("src");
    URL.revokeObjectURL(analysisUrl);
    analysisUrl = undefined;
  }
}

async function prepareRoute() {
  clearAnalysis();
  step = 0;
  ordered = [];
  route = [];
  startInput.value = "";
  document.querySelector("[name='direction'][value='forward']").checked = true;
  try {
    appliedTolerance = positive(el("tolerance"), "Endpoint tolerance");
    route = await request("prepare", { layer: selectedLayer(routeLayer), tolerance: appliedTolerance });
    startInput.max = route.length;
    const lines = route.filter((segment) => segment.type === "LINE").length;
    routeNote = `${route.length} segments in a closed track (${lines} straight, ${route.length - lines} curved).`;
  } catch (error) {
    routeNote = error.message;
  }
  if (mode === "route") {
    status(routeNote, !route.length);
    drawPlot();
  }
}

async function loadCenters() {
  points = [];
  try {
    points = await request("centers", { layer: selectedLayer(circleLayer) });
    const count = points.length;
    circleNote = count
      ? `Found ${count.toLocaleString("en")} circle ${count === 1 ? "center" : "centers"}.`
      : "There are no CIRCLE entities in the selected layers.";
  } catch (error) {
    circleNote = error.message;
  }
  if (mode === "circle") {
    status(circleNote, !points.length && Boolean(drawing.circleCount));
    drawPlot();
  }
}

async function loadDrawing(filename, bytes, sample) {
  status("Loading the processing engine and reading the DXF file…");
  drawing = await request("load", { filename }, bytes, sample === "route");
  el("file-name").textContent = filename;
  el("file-name").title = filename;
  populateLayers(routeLayer, drawing.layers,
    drawing.layers.find((layer) => layer.toLowerCase() === "track") ??
      (drawing.layers.length === 1 ? drawing.layers[0] : ""));
  populateLayers(circleLayer, drawing.circleLayers);
  el("scale").value = el("circle-scale").value = drawing.scale;
  for (const item of document.querySelectorAll(".scale-source")) item.textContent = drawing.scaleSource;
  await prepareRoute();
  await loadCenters();
  selectMode(drawing.circleCount && (sample === "circle" || mode === "circle" || !route.length) ? "circle" : "route");
}

function selectMode(selection) {
  mode = selection;
  if (drawing) status(mode === "route" ? routeNote : circleNote, mode === "route" && !route.length);
  render();
  drawPlot();
}

function render() {
  const isRoute = mode === "route";
  const hasAnalysis = Boolean(analysis && isRoute && step === 3);
  const showingAnalysis = hasAnalysis && view === "analysis";
  dxf.disabled = busy;
  for (const button of navButtons) el(button).disabled = busy;
  for (const field of editing) field.disabled = busy;
  for (const button of exportButtons) button.disabled = busy || (isRoute ? !hasAnalysis : !points.length);
  for (const label of ["route", "circle"]) el(label + "-tab").setAttribute("aria-pressed", String(mode === label));
  el("empty-settings").hidden = Boolean(drawing);
  el("route-settings").hidden = !drawing || !isRoute;
  el("circle-settings").hidden = !drawing || isRoute;
  el("route-exports").hidden = !hasAnalysis;
  el("step-title").textContent = titles[step];
  for (const [index, indicator] of [...el("steps").children].entries()) {
    if (index === step) indicator.setAttribute("aria-current", "step");
    else indicator.removeAttribute("aria-current");
  }
  for (const panel of document.querySelectorAll("[data-step]")) panel.hidden = Number(panel.dataset.step) !== step;
  el("back").hidden = step === 0;
  el("next").hidden = hasAnalysis;
  el("next").disabled = busy || !route.length || el("tolerance").valueAsNumber !== appliedTolerance ||
    (step > 0 && startIndex() === null);
  el("next").textContent = nextLabels[step];
  el("show-map").hidden = el("show-analysis").hidden = !hasAnalysis;
  el("show-map").setAttribute("aria-pressed", String(view === "map"));
  el("show-analysis").setAttribute("aria-pressed", String(view === "analysis"));
  for (const button of viewControls) {
    el(button).hidden = showingAnalysis;
    el(button).disabled = isRoute ? !route.length : !points.length;
  }
  el("map-area").hidden = showingAnalysis;
  el("analysis-plot").hidden = !showingAnalysis;
  el("preview-title").textContent = showingAnalysis ? "Track Analysis" : isRoute ? "Track Preview" : "Circle Center Preview";
  el("preview-meta").textContent = showingAnalysis
    ? `Track length ${analysis.total.toLocaleString("en", { maximumFractionDigits: 2 })} m`
    : isRoute ? "DXF coordinates · Positive Y points up" : "DXF coordinates · Each point is a circle center";
  el("legend").hidden = !isRoute || showingAnalysis || !route.length;
}

function svg(tag, attributes = {}, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  if (text !== undefined) node.textContent = text;
  return node;
}

let camera = null;
let fit = null;
function setCamera() {
  if (camera) map.setAttribute("viewBox", [camera.x, camera.y, camera.width, camera.height].join(" "));
}

function drawPlot(keepView = false) {
  const track = mode === "route" ? (step >= 2 && ordered.length ? ordered : route) : [];
  const coordinates = mode === "circle" ? points : track.flatMap(({ points: segmentPoints }) => segmentPoints);
  map.replaceChildren();
  el("empty-plot").hidden = coordinates.length > 0;
  el("empty-plot").textContent = drawing ? "No entities to preview." : "Load a DXF file to see a preview.";
  if (!coordinates.length) {
    camera = fit = null;
    return;
  }
  let left = Infinity;
  let top = Infinity;
  let right = -Infinity;
  let bottom = -Infinity;
  for (const [x, y] of coordinates) {
    left = Math.min(left, x);
    right = Math.max(right, x);
    top = Math.min(top, -y);
    bottom = Math.max(bottom, -y);
  }
  const span = Math.max(right - left, bottom - top) || 1;
  const margin = span * .07;
  fit = { x: left - margin, y: top - margin, width: right - left + margin * 2, height: bottom - top + margin * 2 };
  if (!keepView || !camera) camera = { ...fit };
  setCamera();
  const plot = document.createDocumentFragment();
  if (mode === "circle") {
    for (const [x, y] of points) {
      const dot = svg("circle", { cx: x, cy: -y, r: span * .005, class: "circle-point" });
      dot.append(svg("title", undefined, x.toPrecision(7) + ", " + y.toPrecision(7)));
      plot.append(dot);
    }
  } else {
    const selected = step === 1 ? startIndex() : 1;
    const selectedSegment = selected ? track[selected - 1].points : null;
    for (const { type, points: segmentPoints } of track) {
      plot.append(svg("polyline", {
        points: segmentPoints.map(([x, y]) => x + "," + -y).join(" "),
        class: type === "ARC" ? "track-arc" : "track-line",
      }));
    }
    if (selectedSegment) {
      const defs = svg("defs");
      const marker = svg("marker", { id: "arrow", orient: "auto", viewBox: "0 0 10 10",
        markerWidth: 3, markerHeight: 3, refX: 9, refY: 5 });
      marker.append(svg("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#bf4c1b" }));
      defs.append(marker);
      plot.append(defs);
      const [x, y] = selectedSegment[0];
      const [endX, endY] = selectedSegment[Math.max(1, Math.floor(selectedSegment.length / 4))];
      plot.append(svg("line", { x1: x, y1: -y, x2: endX, y2: -endY, class: "direction-arrow", "marker-end": "url(#arrow)" }));
    }
    for (const [index, segment] of track.entries()) {
      const [x, y] = segment.points[0];
      const number = index + 1;
      const marked = number === selected;
      const node = svg("g", { class: marked ? "node selected" : "node" });
      node.append(svg("circle", { cx: x, cy: -y, r: span * (marked ? .007 : .004) }));
      node.append(svg("text", {
        x: x + span * .007, y: -y - span * .007, "font-size": span * .018, "stroke-width": span * .002,
      }, number));
      if (step === 1) {
        node.setAttribute("tabindex", "0");
        node.setAttribute("role", "button");
        node.setAttribute("aria-label", `Select junction ${number}`);
        node.addEventListener("click", () => pickStart(number));
        node.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            pickStart(number);
            map.querySelectorAll(".node")[index]?.focus();
          }
        });
      }
      plot.append(node);
    }
  }
  map.append(plot);
}

function pickStart(number) {
  if (busy) return;
  startInput.value = number;
  render();
  drawPlot(true);
}

function zoom(factor) {
  if (!camera) return;
  camera.x += camera.width * (1 - factor) / 2;
  camera.y += camera.height * (1 - factor) / 2;
  camera.width *= factor;
  camera.height *= factor;
  setCamera();
}

let drag;
map.addEventListener("pointerdown", (event) => {
  if (!camera || event.button !== 0 || event.target.closest("[role='button']")) return;
  map.setPointerCapture(event.pointerId);
  drag = { x: event.clientX, y: event.clientY };
});
map.addEventListener("pointermove", (event) => {
  if (!drag || !camera) return;
  const scale = map.getScreenCTM().a;
  camera.x -= (event.clientX - drag.x) / scale;
  camera.y -= (event.clientY - drag.y) / scale;
  drag = { x: event.clientX, y: event.clientY };
  setCamera();
});
for (const event of ["pointerup", "pointercancel", "lostpointercapture"]) map.addEventListener(event, () => { drag = null; });
el("zoom-in").addEventListener("click", () => zoom(.8));
el("zoom-out").addEventListener("click", () => zoom(1.25));
el("zoom-reset").addEventListener("click", () => { if (fit) { camera = { ...fit }; setCamera(); } });

function blobFor(file) {
  return new Blob([Uint8Array.from(atob(file.data), (character) => character.charCodeAt(0))], { type: file.type });
}

function download(file) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blobFor(file));
  link.download = file.filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 30_000);
  status(`Download ready for ${file.filename}`);
}

async function updateOrder() {
  ordered = await request("order", { start: startIndex(), reverse: direction() });
  drawPlot();
}

async function analyze() {
  const scale = positive(el("scale"), "Meters per DXF unit");
  const lateral_g = positive(el("lateral"), "Lateral acceleration");
  status("Analyzing the track…");
  analysis = await request("analysis", { start: startIndex(), reverse: direction(), scale, lateral_g });
  analysisUrl = URL.createObjectURL(blobFor(analysis));
  el("analysis-plot").src = analysisUrl;
  view = "analysis";
  status("Track analysis complete.");
}

async function exportFile(format) {
  if (format === "analysis") { download(analysis); return; }
  const scale = positive(el(mode === "circle" ? "circle-scale" : "scale"), "Meters per DXF unit");
  const args = { mode, export_format: format, scale, ini_options: iniOptions };
  if (mode === "circle") {
    args.layer = selectedLayer(circleLayer);
  } else {
    args.start = startIndex();
    args.reverse = direction();
    if (xyMode.value === "distance") {
      args.spacing = positive(xyValue, "XY sample spacing");
    } else {
      const count = xyValue.valueAsNumber;
      if (!Number.isInteger(count) || count < 2) throw new Error("Enter a whole number of at least 2 points per segment.");
      args.points_per_segment = count;
    }
  }
  status("Preparing the export…");
  download(await request("export", args));
}

dxf.addEventListener("change", () => {
  const file = dxf.files[0];
  if (file) void perform(async () => {
    dxf.value = "";
    await loadDrawing(file.name, await file.arrayBuffer());
  });
});
for (const [sample, name] of [["route", "fsae_A_2025.dxf"], ["circle", "FST_cone.dxf"]]) {
  el(sample + "-sample").addEventListener("click", () => perform(async () => {
    status("Downloading the sample…");
    const response = await fetch("./samples/" + name);
    if (!response.ok) throw new Error("Could not load the sample DXF file.");
    await loadDrawing(name, await response.arrayBuffer(), sample);
  }));
}
el("route-tab").addEventListener("click", () => selectMode("route"));
el("circle-tab").addEventListener("click", () => selectMode("circle"));
routeLayer.addEventListener("change", () => perform(prepareRoute));
circleLayer.addEventListener("change", () => perform(loadCenters));
el("tolerance-form").addEventListener("submit", (event) => { event.preventDefault(); void perform(prepareRoute); });
el("tolerance").addEventListener("input", render);
startInput.addEventListener("input", () => { render(); drawPlot(true); });
for (const radio of document.querySelectorAll("[name='direction']")) {
  radio.addEventListener("change", () => perform(updateOrder));
}
el("next").addEventListener("click", () => perform(async () => {
  if (step === 3) { await analyze(); return; }
  if (step === 1) {
    ordered = await request("order", { start: startIndex(), reverse: direction() });
  }
  step++;
  drawPlot();
}));
el("back").addEventListener("click", () => {
  clearAnalysis();
  step--;
  render();
  drawPlot();
});
for (const [id, other] of [["scale", "circle-scale"], ["circle-scale", "scale"]]) {
  el(id).addEventListener("input", () => { el(other).value = el(id).value; clearAnalysis(); render(); });
}
el("lateral").addEventListener("input", () => { clearAnalysis(); render(); });
el("show-map").addEventListener("click", () => { view = "map"; render(); });
el("show-analysis").addEventListener("click", () => { view = "analysis"; render(); });
xyMode.addEventListener("change", () => {
  const distance = xyMode.value === "distance";
  el("xy-label").textContent = distance ? "Sample spacing (m)" : "Points per segment (including both ends)";
  xyValue.min = distance ? "0" : "2";
  xyValue.step = distance ? "any" : "1";
  xyValue.value = xyOptions[xyMode.value];
});
xyValue.addEventListener("input", () => { xyOptions[xyMode.value] = xyValue.value; });
for (const button of exportButtons) button.addEventListener("click", () => perform(() => exportFile(button.dataset.export)));

const dialog = el("ini-dialog");
const iniForm = el("ini-form");
const iniError = el("ini-error");
const field = (name) => iniForm.elements.namedItem(name);
for (const button of document.querySelectorAll(".ini-settings")) {
  button.addEventListener("click", () => {
    field("height").value = iniOptions.height;
    field("firstModel").value = iniOptions.model_offset + 1;
    field("modelFile").value = iniOptions.model_file;
    field("name").value = iniOptions.name;
    field("rotation").value = iniOptions.rotation.join(", ");
    field("physical").checked = iniOptions.physical;
    iniError.textContent = "";
    dialog.showModal();
  });
}
el("ini-cancel").addEventListener("click", () => dialog.close());
iniForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const angles = field("rotation").value.split(",").map((angle) => angle.trim());
  const rotation = angles.map(Number);
  const model_file = field("modelFile").value.trim();
  const name = field("name").value.trim();
  if (angles.length !== 3 || angles.some((angle) => !angle) || rotation.some((angle) => !Number.isFinite(angle)) ||
      !model_file || !name || !Number.isSafeInteger(field("firstModel").valueAsNumber)) {
    iniError.dataset.error = "true";
    iniError.textContent = "Enter three rotation angles, a model filename, an object name, and a valid first object number.";
    return;
  }
  iniOptions = {
    height: field("height").valueAsNumber, model_offset: field("firstModel").valueAsNumber - 1,
    model_file, name, rotation, physical: field("physical").checked,
  };
  dialog.close();
});

render();
