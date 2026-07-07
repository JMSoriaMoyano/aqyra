import type { ReactNode } from "react";
import { AqyraMark } from "./AqyraMark";
import { DISCIPLINES, type Discipline } from "../disciplines";
import { estadoDisciplina } from "../tema";

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  );
}

export function Rail({
  discipline,
  onDiscipline,
  onLogo,
  onHome,
  thinking,
}: {
  discipline: Discipline;
  onDiscipline: (d: Discipline) => void;
  onLogo: () => void;
  onHome: () => void;
  thinking: boolean;
}) {
  return (
    <nav className="rail">
      <div className="logo-btn" onClick={onLogo} title="Aqyra">
        <AqyraMark size={36} thinking={thinking} />
      </div>

      <div className="ri" onClick={onHome}>
        <Icon><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></Icon>
        <span className="tip">Inicio</span>
      </div>
      <div className="ri">
        <Icon><path d="M12 5v14M5 12h14" /></Icon>
        <span className="tip">Nuevo proyecto</span>
      </div>
      <div className="ri">
        <Icon><path d="M21 12a8 8 0 0 1-11.3 7.3L3 21l1.7-6.7A8 8 0 1 1 21 12z" /></Icon>
        <span className="tip">Conversaciones</span>
      </div>
      <div className="ri on">
        <Icon><path d="M3 21V9l9-6 9 6v12" /><path d="M9 21v-6h6v6" /></Icon>
        <span className="tip">Proyectos</span>
      </div>
      <div className="ri">
        <Icon><circle cx="7" cy="7" r="3" /><circle cx="17" cy="17" r="3" /><path d="M10 10l4 4" /></Icon>
        <span className="tip">Federación</span>
      </div>
      <div className="ri">
        <Icon><path d="M9 12l2 2 4-4M7 3h10l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" /></Icon>
        <span className="tip">Entregables firmables</span>
      </div>

      <div className="sep" />

      {DISCIPLINES.map((d) => {
        const bloqueada = estadoDisciplina(d.id).estado === "bloqueada";
        return (
          <div
            key={d.id}
            className={
              "ri disc" +
              (d.id === discipline.id ? " on" : "") +
              (bloqueada ? " blocked" : "")
            }
            onClick={() => { if (!bloqueada) onDiscipline(d); }}
            aria-disabled={bloqueada}
          >
            <Icon><path d="M3 21V9l9-6 9 6v12" /><path d="M9 21v-6h6v6" /></Icon>
            <span className="dot" style={{ background: d.accent }} />
            <span className="tip">{d.name}{bloqueada ? " · bloqueada (ingesta)" : ""}</span>
          </div>
        );
      })}

      <div className="grow" />

      <div className="ri">
        <Icon><path d="M12 3v3M12 18v3M3 12h3M18 12h3" /><circle cx="12" cy="12" r="3.5" /></Icon>
        <span className="tip">Estado del CDE</span>
      </div>
      <div className="av" title="JM Soria">JM</div>
    </nav>
  );
}
