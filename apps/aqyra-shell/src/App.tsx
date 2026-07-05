import { useEffect, useState } from "react";
import { Rail } from "./components/Rail";
import { Home } from "./components/Home";
import { ViewerPane } from "./components/ViewerPane";
import { DISCIPLINES, hexToInt, hexToRgba, type Discipline } from "./disciplines";

export function App() {
  const [discipline, setDiscipline] = useState<Discipline>(DISCIPLINES[0]);
  const [file, setFile] = useState<File | null>(null);
  const [thinking, setThinking] = useState(false);

  // revestir el --accent de la app según la disciplina (estrategia de skin)
  useEffect(() => {
    const s = document.documentElement.style;
    s.setProperty("--accent", discipline.accent);
    s.setProperty("--accent-soft", hexToRgba(discipline.accent, 0.16));
  }, [discipline]);

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
        onDiscipline={setDiscipline}
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
      </main>
    </div>
  );
}
