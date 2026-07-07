import { useEffect, useState } from "react";
import { Rail } from "./components/Rail";
import { Home } from "./components/Home";
import { VisorChrome } from "./components/VisorChrome";
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

  // Arranca en la vista de visor (como el mockup): auto-carga el Maestro federado de muestra que
  // sirve vite (/federado.ifc). Si no está, se queda en la Home.
  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await fetch("/federado.ifc");
        if (!r.ok) return;
        const buf = await r.blob();
        if (!cancel) setFile(new File([buf], "maestro.ifc"));
      } catch { /* sin muestra → Home */ }
    })();
    return () => { cancel = true; };
  }, []);

  // Sólo se conmuta a disciplinas activas; las bloqueadas por ingesta no cambian el acento.
  function elegirDisciplina(d: Discipline) {
    if (estadoDisciplina(d.id).estado === "activa") setDiscipline(d);
  }

  // el logo «piensa» un instante mientras se abre un modelo (demo del doble uso)
  function openFile(f: File) {
    setThinking(true);
    setFile(f);
    window.setTimeout(() => setThinking(false), 4000);
  }

  return (
    <div className={"frame" + (file ? "" : " home")}>
      <Rail
        discipline={discipline}
        onDiscipline={elegirDisciplina}
        onLogo={() => setFile(null)}
        thinking={thinking}
      />
      {file ? (
        <VisorChrome
          file={file}
          discipline={discipline}
          accentInt={hexToInt(discipline.accent)}
          onHome={() => setFile(null)}
        />
      ) : (
        <Home onOpen={openFile} />
      )}
    </div>
  );
}
