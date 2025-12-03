// static/main.js

document.addEventListener("DOMContentLoaded", () => {
  const API_BASE = "http://127.0.0.1:8000";

  const form = document.getElementById("form-propiedad");
  const supTotalInput = document.getElementById("sup_total");
  const supConstruidaInput = document.getElementById("sup_construida");
  const dormitoriosInput = document.getElementById("dormitorios");
  const banosInput = document.getElementById("banos");
  const estacInput = document.getElementById("estacionamientos");
  const antiguedadInput = document.getElementById("antiguedad");
  const comunaInput = document.getElementById("comuna");
  const bodegasInput = document.getElementById("bodegas");

  const terrazaCheckbox = document.getElementById("terraza");
  const piscinaCheckbox = document.getElementById("piscina");
  const aireCheckbox = document.getElementById("aire_acondicionado");
  const closetsCheckbox = document.getElementById("closets_empotrados");

  const precioEstimadoEl = document.getElementById("precio_estimado");
  const segmentoBoxEl = document.getElementById("segmento_box");
  const similaresBodyEl = document.getElementById("similares_body");
  const listoIcon = document.getElementById("estado-api");

  // ---------------------
  // Helpers
  // ---------------------
  function formatUF(num) {
    if (num === null || num === undefined || isNaN(num)) return "-";
    return (
      num.toLocaleString("es-CL", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + " UF"
    );
  }

  function formatNumber(num, digits = 1) {
    if (num === null || num === undefined || isNaN(num)) return "-";
    return num.toLocaleString("es-CL", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function setPrecio(valorUF) {
    precioEstimadoEl.textContent = formatUF(valorUF);
  }

function setSegmentos(segmentoGlobal, segmentoLocal) {
  if (!segmentoGlobal && !segmentoLocal) {
    segmentoBoxEl.innerHTML = `
      <p><strong>Nombre:</strong> No definido</p>
      <p><strong>Código segmento:</strong> -</p>
      <p><strong>N° propiedades en el segmento:</strong> -</p>
      <p><strong>Precio promedio segmento:</strong> -</p>
      <p><strong>Superficie promedio:</strong> -</p>
      <p><strong>Dormitorios promedio:</strong> -</p>
    `;
    return;
  }

  const g = segmentoGlobal || {};
  const l = segmentoLocal || {};

  segmentoBoxEl.innerHTML = `
    <div class="mb-2">
      <h6 class="fw-bold mb-1">Segmento global (K-Means, mercado completo)</h6>
      <p class="mb-0"><strong>Nombre:</strong> ${g.nombre_segmento || "No definido"}</p>
      <p class="mb-0"><strong>Código cluster K-Means:</strong> ${
        typeof g.cluster === "number" ? g.cluster : "-"
      }</p>
      <p class="mb-0"><strong>N° propiedades en el segmento:</strong> ${
        g.n_propiedades ?? "-"
      }</p>
      <p class="mb-0"><strong>Precio promedio segmento:</strong> ${formatUF(
        g.promedio_uf
      )}</p>
      <p class="mb-0"><strong>Superficie promedio:</strong> ${
        g.promedio_sup_total ? formatNumber(g.promedio_sup_total, 1) + " m²" : "-"
      }</p>
      <p class="mb-0"><strong>Dormitorios promedio:</strong> ${
        g.promedio_dormitorios ? formatNumber(g.promedio_dormitorios, 1) : "-"
      }</p>
    </div>
    <hr/>
    <div>
      <h6 class="fw-bold mb-1">Segmento por comuna (ranking de comunas)</h6>
      <p class="mb-0"><strong>Comuna:</strong> ${l.comuna || "-"}</p>
      <p class="mb-0"><strong>Código segmento comuna:</strong> ${
        l.segmento_codigo ?? "-"
      }</p>
      <p class="mb-0"><strong>Nombre segmento comuna:</strong> ${
        l.segmento_nombre || "No definido"
      }</p>
      <p class="mb-0"><strong>N° propiedades en la comuna:</strong> ${
        l.n_propiedades_comuna ?? "-"
      }</p>
      <p class="mb-0"><strong>Precio promedio comuna:</strong> ${formatUF(
        l.precio_promedio_comuna
      )}</p>
      <p class="mb-0"><strong>Superficie promedio comuna:</strong> ${
        l.sup_promedio_comuna
          ? formatNumber(l.sup_promedio_comuna, 1) + " m²"
          : "-"
      }</p>
      <p class="mb-0"><strong>Dormitorios promedio comuna:</strong> ${
        l.dormitorios_promedio_comuna
          ? formatNumber(l.dormitorios_promedio_comuna, 1)
          : "-"
      }</p>
    </div>
  `;
}


  function setSimilares(similares) {
    similaresBodyEl.innerHTML = "";

    if (!Array.isArray(similares) || similares.length === 0) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 8;
      cell.textContent =
        "No se encontraron propiedades similares para estos datos.";
      row.appendChild(cell);
      similaresBodyEl.appendChild(row);
      return;
    }

    similares.forEach((p) => {
      const row = document.createElement("tr");

      function addCell(text) {
        const td = document.createElement("td");
        td.textContent = text;
        row.appendChild(td);
      }

      addCell(p.id_propiedad ?? "-");
      addCell(p.comuna ?? "-");
      addCell(p.sup_total ?? "-");
      addCell(p.dormitorios ?? "-");
      addCell(p.banos ?? "-");
      addCell(p.estacionamientos ?? "-");
      addCell(
        p.precio_en_uf
          ? p.precio_en_uf.toLocaleString("es-CL", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })
          : "-"
      );

      const linkTd = document.createElement("td");
      if (p.url_portal) {
        const a = document.createElement("a");
        a.href = p.url_portal;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.textContent = "Ver ficha";
        linkTd.appendChild(a);
      } else {
        linkTd.textContent = "-";
      }
      row.appendChild(linkTd);

      similaresBodyEl.appendChild(row);
    });
  }

  // ---------------------
  // Comprobar API viva
  // ---------------------
  fetch(`${API_BASE}/health`)
    .then((res) => {
      if (res.ok && listoIcon) {
        listoIcon.classList.remove("text-danger");
        listoIcon.classList.add("text-success");
        listoIcon.textContent = "Listo ✅";
      }
    })
    .catch(() => {
      if (listoIcon) {
        listoIcon.classList.remove("text-success");
        listoIcon.classList.add("text-danger");
        listoIcon.textContent = "Sin conexión a API";
      }
    });

  // ---------------------
  // Submit
  // ---------------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const payload = {
      sup_total: parseFloat(supTotalInput.value) || 0,
      sup_construida: parseFloat(supConstruidaInput.value) || 0,
      dormitorios: parseInt(dormitoriosInput.value || "0", 10),
      banos: parseInt(banosInput.value || "0", 10),
      estacionamientos: parseInt(estacInput.value || "0", 10),
      antiguedad: parseInt(antiguedadInput.value || "0", 10),
      comuna: (comunaInput.value || "").trim().toLowerCase(),
      bodegas: parseInt(bodegasInput.value || "0", 10),

      terraza: terrazaCheckbox.checked,
      piscina: piscinaCheckbox.checked,
      aire_acondicionado: aireCheckbox.checked,
      closets_empotrados: closetsCheckbox.checked,
    };

    try {
      setPrecio(null);
      setSegmentos(null, null);
      setSimilares([]);

      const [predRes, segRes, simRes] = await Promise.all([
        fetch(`${API_BASE}/predict`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`${API_BASE}/segmento`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`${API_BASE}/similar?k=5`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      ]);

      const predData = predRes.ok ? await predRes.json() : null;
      const segData = segRes.ok ? await segRes.json() : null;
      const simData = simRes.ok ? await simRes.json() : null;

      if (predData) {
        setPrecio(predData.precio_estimado_uf);
      }

      if (segData) {
        setSegmentos(segData.segmento_global, segData.segmento_local);
      }

      if (simData) {
        setSimilares(simData.similares);
      }
    } catch (err) {
      console.error("Error al consultar la API:", err);
      setPrecio(null);
      setSegmentos(null, null);
      setSimilares([]);
    }
  });
});
