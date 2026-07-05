import { useRef, useState, type ReactNode } from "react";
import { AqyraMark } from "./AqyraMark";

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  );
}

export function Home({ onOpen }: { onOpen: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function pick(files: FileList | null) {
    const f = files?.[0];
    if (f) onOpen(f);
  }

  return (
    <div className="stage">
      <div className="center">
        <div className="greet">
          <AqyraMark size={38} />
          <h1>¡Bienvenido, JM!</h1>
        </div>

        <div className="box">
          <div className="input">
            <span className="caret" />
            <span className="ph">
              Háblale a tu proyecto · escribe&nbsp;<span className="slash">/</span>&nbsp;para habilidades
            </span>
          </div>
          <div className="bottom">
            <div className="icobtn" title="Adjuntar IFC" onClick={() => inputRef.current?.click()}>
              <Icon><path d="M12 5v14M5 12h14" /></Icon>
            </div>
            <div className="spacer" />
            <div className="selbtn">
              <span className="mname">Aqyra Golden</span> Alto
              <Icon><path d="M6 9l6 6 6-6" /></Icon>
            </div>
            <div className="icobtn" title="Dictar">
              <Icon><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M6 11a6 6 0 0 0 12 0M12 17v4" /></Icon>
            </div>
            <div className="send" title="Enviar">
              <Icon><path d="M12 19V5M5 12l7-7 7 7" /></Icon>
            </div>
          </div>
        </div>

        {/* Slice 1 · abrir un IFC suelto */}
        <div
          className={"dropzone" + (over ? " over" : "")}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); pick(e.dataTransfer.files); }}
        >
          Arrastra aquí un <b>.ifc</b> o haz clic para abrirlo en <b>el visor abierto</b>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".ifc"
          style={{ display: "none" }}
          onChange={(e) => pick(e.target.files)}
        />

        <div className="chips">
          <div className="chip" onClick={() => inputRef.current?.click()}>
            <Icon><path d="M3 21V9l9-6 9 6v12" /></Icon>Abrir modelo
          </div>
          <div className="chip">
            <Icon><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></Icon>Compañero AEC
          </div>
          <div className="chip">
            <Icon><path d="M12 3v12M8 11l4 4 4-4M5 21h14" /></Icon>Narración → IFC
          </div>
          <div className="chip">
            <Icon><path d="M9 12l2 2 4-4M7 3h10l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" /></Icon>Memoria firmable
          </div>
        </div>

        <div className="hint">
          Slice 1 · <b>abre un IFC suelto</b> en el visor real — el resto del ecosistema se conecta por olas
        </div>
      </div>
    </div>
  );
}
