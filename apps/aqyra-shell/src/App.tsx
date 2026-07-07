import { useEffect, useState } from "react";
import { Rail } from "./components/Rail";
import { Home } from "./components/Home";
import { ViewerPane } from "./components/ViewerPane";
import { Footer } from "./components/Footer";
import { DISCIPLINES, hexToInt, type Discipline } from "./disciplines";
import { temaDisciplina, estadoDisciplina } from "./tema";

export function App() {
  const [discipline, setDiscipline] = useState<Discipline>(DISCIPLINES[0]);
  const [file, setFile] = useState<File | null>(null);
  const [thinking, setThinking] = useState(false);

  // Tematización del chrome por disciplina (D-CH-2): el acento tiñe `--acc`/`--acc-soft`.
  // Se mantiene `--accent`/`--accent-soft` como alias para el CSS heredado del shell.
  useEffect(() => {
    const { acc, accSoft } = temaDisciplina(discipline.id);
    const s = document.documentElement.style;
    s.setProperty("--acc", acc);
    s.setProperty("--acc-soft", accSoft);
    s.setProperty("--accent", acc);
    s.setProperty("--accent-soft", accSoft);
  }, [discipline]);

  // Sólo se conmuta a disciplinas activas; las bloqueadas por ingesta no cambian el acento.
  function elegirDisciplina(d: Discipline) {
    if (estadoDisciplina(d.id).estado === "activa") setDiscipline(d);
  }

  // el logo «piensa» un instante mientras se abre un modelo (demo del doble uso)
  function openFile(f: File) {
    setThinking(true);
    setFile(f);
    window.setTimeout(() => setThinking(false), 6200);
  }

  return (
    <div className="app">
      <Rail
        discipline={discipline}
        onDiscipline={elegirDisciplina}
        onLogo={() => setThinking((t) => !t)}
        onHome={() => setFile(null)}
        thinking={thinking}
      />
      <main className="main">
        <div className="topstrip">
          <div className="crumb">
            {file ? (
              <>
                <span className="link" onClick={() => setFile(null)}>Inicio</span> / <b>{file.name}</b>
              </>
            ) : (
              <b>Inicio</b>
            )}
          </div>
          <div className="disc-pill">
            <span className="d" />
            <span>{discipline.name}</span>
          </div>
        </div>

        {file ? (
          <ViewerPane file={file} accentInt={hexToInt(discipline.accent)} />
        ) : (
          <Home onOpen={openFile} />
        )}

        <Footer />
      </main>
    </div>
  );
}
