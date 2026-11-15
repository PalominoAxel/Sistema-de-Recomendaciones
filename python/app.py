"""Interfaz web (Streamlit) del Motor de Recomendacion.

Python sigue siendo el orquestador: esta app solo es la capa visual
encima de los mismos puentes que usa main.py.
  - Scala  (scala_bridge.MotorScala.cotizar): catalogo, precios con
    descuento segun tipo de cliente y total del carrito.
  - Prolog (prolog_bridge.MotorPrologo): herencia, propiedades,
    accesorios recomendados y la red semantica completa.

Ejecutar desde la raiz del proyecto:
    python -m streamlit run python/app.py
"""

import time

import streamlit as st

from modelos import CLIENTES_DISPONIBLES
from prolog_bridge import MotorPrologo
from scala_bridge import MotorScala

st.set_page_config(page_title="Motor de Recomendación", page_icon="🛍️", layout="wide")

ICONOS = {
    "laptop": "💻", "smartphone": "📱", "tablet": "📲", "television": "📺",
    "camisa": "👔", "pantalon": "👖", "chaqueta": "🧥", "zapatos": "👟",
    "silla": "🪑", "mesa": "🍽️", "lampara": "💡",
}
COLORES_CATEGORIA = {"electronica": "#3b82f6", "ropa": "#ec4899", "hogar": "#f59e0b"}

st.markdown(
    """
<style>
.tarjeta {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:14px 16px;
          margin-bottom:6px; background:rgba(128,128,128,.04);}
.tarjeta .icono {font-size:2.2rem; line-height:1;}
.tarjeta .nombre {font-weight:700; font-size:1.05rem; margin:6px 0 2px;}
.chip {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem;
       color:white; margin-right:4px;}
.precio {font-size:1.35rem; font-weight:800;}
.tachado {text-decoration:line-through; opacity:.55; font-size:.9rem; margin-left:6px;}
.dcto {color:#16a34a; font-weight:700; font-size:.85rem; margin-left:6px;}
.stock-ok {color:#16a34a; font-size:.8rem;}
.stock-no {color:#dc2626; font-size:.8rem; font-weight:700;}
.cadena {font-size:1.05rem;}
.cadena b {padding:3px 10px; border-radius:8px; background:rgba(59,130,246,.15);}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- llamadas
# Cada llamada a Scala/Prolog es un subprocess (algunos segundos), asi
# que se cachean: misma entrada -> misma respuesta (funciones puras).

@st.cache_data(show_spinner=False)
def cotizar(tipo: str, nombre: str, items: tuple):
    inicio = time.perf_counter()
    cotizacion = MotorScala().cotizar(tipo, nombre, dict(items))
    return cotizacion, time.perf_counter() - inicio


@st.cache_resource(show_spinner=False)
def motor_prolog(hechos: tuple) -> MotorPrologo:
    motor = MotorPrologo()
    motor.construir_base_conocimiento(list(hechos))
    return motor


@st.cache_data(show_spinner=False)
def consultar(hechos: tuple, producto: str) -> dict:
    return motor_prolog(hechos).consultar_producto(producto)


@st.cache_data(show_spinner=False)
def red_semantica(hechos: tuple) -> dict:
    return motor_prolog(hechos).exportar_red()


def bonito(atomo: str) -> str:
    return atomo.replace("_", " ").capitalize()


# ---------------------------------------------------------------- estado
estado = st.session_state
estado.setdefault("carrito", {})        # {id_producto: cantidad}
estado.setdefault("cotizacion_final", None)

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🛍️ Motor de Recomendación")
    st.caption("Python orquesta · Scala calcula · Prolog razona")

    nombre = st.text_input("Tu nombre", value=estado.get("nombre", ""), placeholder="Escribe tu nombre")
    estado.nombre = nombre
    clases = list(CLIENTES_DISPONIBLES.values())
    clase = st.radio(
        "Tipo de cliente", clases, format_func=lambda c: c.tipo.capitalize(), horizontal=True
    )
    cliente = clase(nombre.strip() or "Invitado")
    st.info(f"**{cliente.nombre}** · {cliente.beneficio()}")

with st.spinner("Ejecutando Módulo Scala (precios para tu tipo de cliente)..."):
    cotizacion, segundos_scala = cotizar(cliente.tipo, "catalogo", ())
catalogo = cotizacion.catalogo
por_id = {p.id: p for p in catalogo}
hechos = tuple(cotizacion.hechos_prolog)
with st.spinner("Preparando base de conocimiento Prolog..."):
    motor_prolog(hechos)

with st.sidebar:
    st.divider()
    st.subheader("Filtros")
    categorias = sorted({p.categoria for p in catalogo})
    elegidas = st.multiselect("Categorías", categorias, default=categorias, format_func=bonito)
    tope = max(p.precio for p in catalogo)
    rango = st.slider("Rango de precio final ($)", 0.0, float(tope), (0.0, float(tope)), step=10.0)
    solo_stock = st.toggle("Solo con stock", value=False)
    st.divider()
    unidades = sum(estado.carrito.values())
    st.metric("🛒 Carrito", f"{unidades} unidad(es)")
    st.caption(f"Scala respondió en {segundos_scala:.1f}s · {len(catalogo)} productos · "
               f"{len(hechos)} hechos es_un/2 enviados a Prolog")


# ---------------------------------------------------------------- dialogos
@st.dialog("Recomendación del Módulo Prolog", width="large")
def ver_recomendacion(producto):
    with st.spinner("Consultando Prolog..."):
        datos = consultar(hechos, producto.nombre)
    st.markdown(f"### {ICONOS.get(producto.subtipo, '📦')} {producto.nombre_legible}")
    cadena = " → ".join(f"<b>{bonito(x)}</b>" for x in [producto.nombre, *datos["categorias"]])
    st.markdown("**Herencia (`es_un_transitivo/2`)**")
    st.markdown(f"<div class='cadena'>{cadena}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Propiedades heredadas (`tiene_propiedad/2`)**")
        for prop in datos["propiedades"]:
            st.markdown(f"- {bonito(prop)}")
    with c2:
        st.markdown("**Accesorios recomendados (`recomendar_accesorio/2`)**")
        for acc in datos["accesorios"] or ["(ninguno)"]:
            st.markdown(f"- 🧩 {bonito(acc)}")
    st.graphviz_chart(grafo_producto(producto, datos), width="stretch")


def grafo_producto(producto, datos) -> str:
    lineas = ['digraph{rankdir=LR; bgcolor="transparent";',
              'node[style="rounded,filled" shape=box fontname="Helvetica" fontsize=11];',
              'edge[color="#94a3b8" fontcolor="#94a3b8" fontsize=9];']
    camino = [producto.nombre, *datos["categorias"]]
    for nodo in camino:
        lineas.append(f'"{nodo}"[fillcolor="#bfdbfe"];')
    lineas[-len(camino)] = f'"{producto.nombre}"[fillcolor="#3b82f6" fontcolor="white"];'
    for a, b in zip(camino, camino[1:]):
        lineas.append(f'"{a}"->"{b}"[label="es_un" color="#3b82f6" penwidth=2];')
    for acc in datos["accesorios"]:
        lineas.append(f'"{acc}"[shape=note fillcolor="#fed7aa"];')
        lineas.append(f'"{producto.subtipo}"->"{acc}"[label="compatible" style=dashed];')
    lineas.append("}")
    return "\n".join(lineas)


def agregar(producto):
    actual = estado.carrito.get(producto.id, 0)
    if actual >= producto.stock:
        st.toast(f"No hay más stock de {producto.nombre_legible}", icon="⚠️")
        return
    estado.carrito[producto.id] = actual + 1
    estado.cotizacion_final = None
    datos = consultar(hechos, producto.nombre)
    sugeridos = ", ".join(bonito(a) for a in datos["accesorios"][:3])
    st.toast(f"Agregado: {producto.nombre_legible}", icon="🛒")
    if sugeridos:
        st.toast(f"Prolog sugiere acompañarlo con: {sugeridos}", icon="🧠")


# ---------------------------------------------------------------- pestañas
tab_catalogo, tab_carrito, tab_red, tab_como = st.tabs(
    ["🛍️ Catálogo", f"🛒 Carrito ({unidades})", "🕸️ Red semántica", "⚙️ Cómo funciona"]
)

with tab_catalogo:
    visibles = [
        p for p in catalogo
        if p.categoria in elegidas
        and rango[0] <= p.precio_final <= rango[1]
        and (p.stock > 0 or not solo_stock)
    ]
    st.caption(f"Mostrando {len(visibles)} de {len(catalogo)} productos · "
               f"precios calculados por Scala para cliente **{cliente.tipo}**")
    columnas = st.columns(3)
    for indice, p in enumerate(visibles):
        with columnas[indice % 3]:
            color = COLORES_CATEGORIA.get(p.categoria, "#64748b")
            descuento = (f"<span class='tachado'>${p.precio:,.2f}</span>"
                         f"<span class='dcto'>-{p.descuento:.0%}</span>") if p.descuento else ""
            stock = (f"<span class='stock-ok'>● {p.stock} en stock</span>" if p.stock
                     else "<span class='stock-no'>● Agotado</span>")
            st.markdown(
                f"""<div class='tarjeta'>
                <div class='icono'>{ICONOS.get(p.subtipo, '📦')}</div>
                <div class='nombre'>{p.nombre_legible}</div>
                <span class='chip' style='background:{color}'>{bonito(p.categoria)}</span>
                <span class='chip' style='background:#64748b'>{bonito(p.subtipo)}</span>
                <div style='margin-top:8px'><span class='precio'>${p.precio_final:,.2f}</span>{descuento}</div>
                {stock}</div>""",
                unsafe_allow_html=True,
            )
            b1, b2 = st.columns(2)
            if b1.button("🧠 Recomendar", key=f"rec{p.id}", width="stretch"):
                ver_recomendacion(p)
            if b2.button("➕ Agregar", key=f"add{p.id}", width="stretch",
                         disabled=p.stock == 0, type="primary"):
                agregar(p)
                st.rerun()

with tab_carrito:
    if not estado.carrito:
        st.info("Tu carrito está vacío. Agrega productos desde el catálogo.")
    else:
        for id_, cantidad in list(estado.carrito.items()):
            p = por_id[id_]
            c1, c2, c3, c4 = st.columns([5, 2, 2, 1])
            c1.markdown(f"{ICONOS.get(p.subtipo, '📦')} **{p.nombre_legible}**  \n"
                        f"<small>${p.precio_final:,.2f} c/u</small>", unsafe_allow_html=True)
            nueva = c2.number_input("Cantidad", 1, p.stock, cantidad, key=f"cant{id_}",
                                    label_visibility="collapsed")
            if nueva != cantidad:
                estado.carrito[id_] = nueva
                estado.cotizacion_final = None
                st.rerun()
            c3.markdown(f"**${p.precio_final * cantidad:,.2f}**")
            if c4.button("🗑️", key=f"del{id_}"):
                del estado.carrito[id_]
                estado.cotizacion_final = None
                st.rerun()

        st.divider()
        if st.button("💳 Calcular total con Scala", type="primary"):
            with st.spinner("Scala está calculando el carrito (map + sum + pattern matching)..."):
                estado.cotizacion_final, _ = cotizar(
                    cliente.tipo, cliente.nombre, tuple(sorted(estado.carrito.items()))
                )
        final = estado.cotizacion_final
        if final:
            m1, m2, m3 = st.columns(3)
            m1.metric("Subtotal sin descuento", f"${final.subtotal:,.2f}")
            m2.metric("Ahorro", f"${final.ahorro:,.2f}",
                      f"{final.ahorro / final.subtotal:.1%}" if final.subtotal else None)
            m3.metric("TOTAL", f"${final.total:,.2f}")
            st.success(f"Total calculado por `calcularTotalCarrito` (Scala) para "
                       f"{cliente.nombre} (cliente {cliente.tipo}).")
        else:
            st.caption("El total oficial lo calcula Scala; presiona el botón para obtenerlo.")

        st.subheader("🧠 Completa tu compra")
        sugerencias = {}
        for id_ in estado.carrito:
            for acc in consultar(hechos, por_id[id_].nombre)["accesorios"]:
                sugerencias.setdefault(acc, []).append(por_id[id_].nombre_legible)
        if sugerencias:
            cols = st.columns(3)
            for i, (acc, origen) in enumerate(sugerencias.items()):
                cols[i % 3].markdown(f"🧩 **{bonito(acc)}**  \n<small>para {', '.join(origen)}</small>",
                                     unsafe_allow_html=True)

with tab_red:
    red = red_semantica(hechos)
    c1, c2, c3 = st.columns([2, 2, 3])
    categoria_red = c1.selectbox("Categoría", ["todas", *categorias], format_func=bonito)
    candidatos = [p for p in catalogo if categoria_red in ("todas", p.categoria)]
    destacado = c2.selectbox("Resaltar producto", ["(ninguno)", *[p.nombre for p in candidatos]],
                             format_func=lambda n: n if n == "(ninguno)" else bonito(n))
    with c3:
        ver_props = st.checkbox("Mostrar propiedades", value=True)
        ver_accs = st.checkbox("Mostrar accesorios compatibles", value=categoria_red != "todas")

    camino = set()
    if destacado != "(ninguno)":
        camino = {destacado, *consultar(hechos, destacado)["categorias"]}

    def dentro(nodo: str) -> bool:
        if categoria_red == "todas":
            return True
        return nodo in ("producto", categoria_red) or any(
            nodo in (p.nombre, p.subtipo) for p in candidatos)

    instancias = {p.nombre for p in catalogo}
    dot = ['digraph{rankdir=LR; bgcolor="transparent"; nodesep=0.15; ranksep=0.6;',
           'node[style="rounded,filled" shape=box fontname="Helvetica" fontsize=10 fillcolor="#e2e8f0"];',
           'edge[color="#94a3b8" arrowsize=0.6];']
    nodos = set()
    for hijo, padre in red["ES_UN"]:
        if dentro(hijo) and dentro(padre):
            nodos |= {hijo, padre}
            resaltar = hijo in camino and padre in camino
            dot.append(f'"{hijo}"->"{padre}"' + ('[color="#ef4444" penwidth=2.5];' if resaltar else ";"))
    for nodo in nodos:
        if nodo in camino:
            relleno = '"#ef4444" fontcolor="white"'
        elif nodo == "producto":
            relleno = '"#1e293b" fontcolor="white"'
        elif nodo in COLORES_CATEGORIA:
            relleno = f'"{COLORES_CATEGORIA[nodo]}" fontcolor="white"'
        elif nodo in instancias:
            relleno = '"#f1f5f9"'
        else:
            relleno = '"#cbd5e1"'
        dot.append(f'"{nodo}"[fillcolor={relleno}];')
    if ver_props:
        for origen, prop in red["PROPIEDAD"]:
            if origen in nodos:
                dot.append(f'"p_{prop}"[label="{prop}" shape=ellipse fillcolor="#bbf7d0"];')
                dot.append(f'"{origen}"->"p_{prop}"[style=dotted color="#16a34a"];')
    if ver_accs:
        for origen, acc in red["COMPATIBLE"]:
            if origen in nodos:
                dot.append(f'"a_{acc}"[label="{acc}" shape=note fillcolor="#fed7aa"];')
                dot.append(f'"{origen}"->"a_{acc}"[style=dashed color="#f97316"];')
    dot.append("}")
    st.graphviz_chart("\n".join(dot), width="stretch")
    st.caption("Flechas sólidas: `es_un/2` · punteadas verdes: `propiedad/2` · "
               "discontinuas naranjas: `compatible/2`. Todos los arcos vienen de Prolog (`exportar_red/0`).")

with tab_como:
    st.subheader("Arquitectura multiparadigma")
    st.graphviz_chart(
        """digraph{rankdir=LR; bgcolor="transparent";
        node[shape=box style="rounded,filled" fontname="Helvetica" fontsize=11];
        edge[fontname="Helvetica" fontsize=9 color="#94a3b8" fontcolor="#64748b"];
        u[label="👤 Usuario\\n(navegador)" fillcolor="#e2e8f0"];
        py[label="Python (POO)\\nOrquestador + Streamlit" fillcolor="#fde68a"];
        sc[label="Scala (Funcional)\\nfilter · map · pattern matching" fillcolor="#fecaca"];
        pl[label="Prolog (Lógico)\\nred semántica · inferencia" fillcolor="#bfdbfe"];
        u->py[label="clics"]; py->u[label="interfaz"];
        py->sc[label="cotizar tipo cliente carrito"]; sc->py[label="PRECIO / ITEM / TOTAL\\nhechos es_un/2"];
        py->pl[label="catalogo_generado.pl\\n+ consulta"]; pl->py[label="CATEGORIA / PROPIEDAD\\nACCESORIO"];
        }""",
        width="stretch",
    )
    st.markdown(
        "1. **Scala** recibe el tipo de cliente y el carrito, aplica descuentos con *pattern matching* "
        "y traduce el catálogo a hechos `es_un/2`.\n"
        "2. **Python** combina esos hechos con `red_semantica.pl` y genera `catalogo_generado.pl`.\n"
        "3. **Prolog** infiere herencia, propiedades y accesorios por resolución y unificación.\n"
        "4. **Python** une ambas respuestas y las muestra en esta interfaz."
    )
    with st.expander(f"Hechos Prolog generados por Scala ({len(hechos)})"):
        st.code("\n".join(hechos), language="prolog")
