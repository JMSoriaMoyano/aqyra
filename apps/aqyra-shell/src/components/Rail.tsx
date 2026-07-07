import { AqyraMark } from "./AqyraMark";
import { DISCIPLINES, type Discipline } from "../disciplines";
import { estadoDisciplina } from "../tema";

/** Rail del mockup v0.6: logo Aqyra + conmutador de disciplina (swatch + tooltip). Diseño y
 *  Estructuras activas; Instalaciones/Obras lineales/Puentes atenuadas (bloqueadas por ingesta). */
export function Rail({
  discipline,
  onDiscipline,
  onLogo,
  thinking,
}: {
  discipline: Discipline;
  onDiscipline: (d: Discipline) => void;
  onLogo: () => void;
  thinking: boolean;
}) {
  return (
    <nav className="rail">
      <div className="mark" onClick={onLogo} title="Aqyra — inicio">
        <AqyraMark size={28} thinking={thinking} />
      </div>

      {DISCIPLINES.map((d) => {
        const bloqueada = estadoDisciplina(d.id).estado === "bloqueada";
        return (
          <div
            key={d.id}
            className={"db" + (d.id === discipline.id ? " on" : "") + (bloqueada ? " blocked" : "")}
            onClick={() => { if (!bloqueada) onDiscipline(d); }}
            aria-disabled={bloqueada}
          >
            <span className="sw" style={{ background: d.accent }} />
            <span className="tip">{d.name}{bloqueada ? " · bloqueada (ingesta)" : ""}</span>
          </div>
        );
      })}

      <div className="grow" />
      <div className="av" title="JM Soria">JM</div>
    </nav>
  );
}
