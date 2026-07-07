import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./tokens.css";
import "./chrome.css";

// Sin StrictMode: evita el doble montaje en dev, que reinicializa el visor WebGL
// (web-ifc + three) dos veces y enturbia el primer encuadre de la cámara.
createRoot(document.getElementById("root")!).render(<App />);
