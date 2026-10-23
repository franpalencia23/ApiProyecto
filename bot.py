"""
bot.py - Bot de Telegram que controla el ESP32 con lenguaje natural (Punto 4 del parcial)

Flujo:
  Telegram --> bot.py --> Ollama (LLM local: detecta la INTENCION del mensaje)
                           |-- encender_led / apagar_led / leer_sensor --> MQTT (Mosquitto) --> ESP32
                           |-- ultimo_registro / promedio_24h        --> API (FastAPI en Render) --> BD
Reglas de arquitectura:
  * El bot NO se conecta a la base de datos: consulta siempre la API.
  * El LLM solo decide la intencion; las acciones las ejecuta codigo fijo
    (el modelo nunca construye SQL ni comandos libres).
"""
import json
import os
import queue
import re
import time

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:          # python-dotenv es opcional si las variables ya estan en el entorno
    pass

# ----------------------------------------------------------------------
# Configuracion (.env)
# ----------------------------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_API = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
ALLOWED_CHAT_IDS = {int(x) for x in os.getenv("ALLOWED_CHAT_IDS", "").replace(" ", "").split(",") if x}

API_BASE = os.getenv("API_BASE_URL", "https://apiproyectoestresh.onrender.com/api/v1").rstrip("/")
BOT_EMAIL = os.getenv("BOT_EMAIL", "")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_COMANDOS = "iot/estres_hidrico/comandos"
TOPIC_ESTADO = "iot/estres_hidrico/estado"
ESPERA_ESP32_S = float(os.getenv("ESPERA_ESP32_S", "6"))

# ----------------------------------------------------------------------
# 1. LLM: deteccion de intencion
# ----------------------------------------------------------------------
INTENCIONES = ["encender_led", "apagar_led", "leer_sensor", "ultimo_registro", "promedio_24h",
               "resumen_dia", "distribucion_estados", "recomendar_riego", "ayuda", "desconocido"]

PROMPT_SISTEMA = """Eres el clasificador de intenciones de un bot de Telegram que controla un ESP32 \
con sensores de humedad y temperatura del suelo y un LED interno. Lee el mensaje del usuario \
(en español, con cualquier forma de hablar) y responde SOLO un JSON: {"intent": "<intencion>"}.

Intenciones posibles:
- encender_led: el usuario quiere ENCENDER / prender / activar el LED o la luz.
- apagar_led: el usuario quiere APAGAR / desactivar el LED o la luz.
- leer_sensor: quiere saber la lectura ACTUAL, en este momento, de los sensores (humedad, temperatura).
- ultimo_registro: quiere el ULTIMO registro / dato / medicion GUARDADO en la base de datos.
- promedio_24h: quiere el promedio o resumen de las ultimas 24 horas / del dia.
- resumen_dia: quiere los valores MAXIMO y MINIMO (los picos) de humedad y temperatura del dia.
- distribucion_estados: quiere saber que porcentaje del tiempo el suelo estuvo en cada estado (optimo, precaucion, estres, critico), o como ha estado el suelo en general / en el historial.
- recomendar_riego: pregunta si debe regar, cuando regar, o pide una recomendacion o consejo para el cultivo o el suelo.
- ayuda: saluda o pregunta que puede hacer el bot / pide ayuda / comandos.
- desconocido: cualquier otra cosa, o si NO esta claro que quiere (incluye negaciones como "no enciendas nada").

Ejemplos:
"enciende el LED" -> encender_led
"prende el led" -> encender_led
"porfa enciéndeme el led" -> encender_led
"activa la luz" -> encender_led
"apaga el led" -> apagar_led
"apaga la luz" -> apagar_led
"ya no quiero luz, quítala" -> apagar_led
"¿cómo está la humedad ahora?" -> leer_sensor
"dame la temperatura actual" -> leer_sensor
"lee el sensor" -> leer_sensor
"cuál fue el último dato guardado" -> ultimo_registro
"muéstrame el último registro" -> ultimo_registro
"cómo estuvo el promedio de hoy" -> promedio_24h
"resumen de las últimas 24 horas" -> promedio_24h
"cuál fue la humedad más alta y más baja de hoy" -> resumen_dia
"dame el máximo y el mínimo del día" -> resumen_dia
"cómo ha estado el suelo en general" -> distribucion_estados
"qué porcentaje del tiempo estuvo en estrés" -> distribucion_estados
"debería regar hoy" -> recomendar_riego
"dame una recomendación de riego" -> recomendar_riego
"hola, qué puedes hacer" -> ayuda
"cuéntame un chiste" -> desconocido
"no enciendas el led" -> desconocido
"qué hora es" -> desconocido"""

ESQUEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": INTENCIONES}},
    "required": ["intent"],
}


def detectar_intencion_llm(texto: str) -> str:
    """Pregunta a Ollama (local) y devuelve una intencion valida. Lanza excepcion si falla."""
    r = requests.post(
        OLLAMA_URL + "/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": ESQUEMA,                 # fuerza JSON con intencion de la lista
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": texto},
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    contenido = r.json()["message"]["content"]
    try:
        intent = json.loads(contenido).get("intent", "desconocido")
    except json.JSONDecodeError:
        m = re.search(r'"intent"\s*:\s*"(\w+)"', contenido)
        intent = m.group(1) if m else "desconocido"
    return intent if intent in INTENCIONES else "desconocido"


def detectar_intencion_reglas(texto: str) -> str:
    """Respaldo SIMPLE por palabras clave, solo si Ollama no responde."""
    t = texto.lower()
    if re.search(r"\bno\b.*\b(enci|prend|apag)", t):
        return "desconocido"
    if re.search(r"apag|quita|desactiv|off", t):
        return "apagar_led"
    if re.search(r"enci[eé]nd|prend|activ|\bon\b", t):
        return "encender_led"
    if re.search(r"m[aá]xim|m[ií]nim|picos?|m[aá]s (alta|alto|baja|bajo)", t):
        return "resumen_dia"
    if re.search(r"porcentaje|distribuci|historial|en general|cu[aá]nto tiempo|estados", t):
        return "distribucion_estados"
    if re.search(r"rieg|regar|recomend|consejo", t):
        return "recomendar_riego"
    if re.search(r"24|promedio|resumen", t):
        return "promedio_24h"
    if re.search(r"[uú]ltim|guardad|registro", t):
        return "ultimo_registro"
    if re.search(r"humedad|temperatura|sensor|lectura|ahora", t):
        return "leer_sensor"
    if re.search(r"hola|ayuda|qu[eé] puedes|comandos|/start", t):
        return "ayuda"
    return "desconocido"


# ----------------------------------------------------------------------
# 2. MQTT -> ESP32
# ----------------------------------------------------------------------
import paho.mqtt.client as mqtt  # noqa: E402

eventos = queue.Queue()          # mensajes que el ESP32 publica en TOPIC_ESTADO


def _al_conectar(client, userdata, *args):
    client.subscribe(TOPIC_ESTADO)


def _al_mensaje(client, userdata, msg):
    try:
        eventos.put(json.loads(msg.payload.decode()))
    except Exception:
        pass


def crear_cliente_mqtt():
    try:                                     # paho-mqtt 2.x
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="bot-telegram-estres")
    except AttributeError:                   # paho-mqtt 1.x
        c = mqtt.Client(client_id="bot-telegram-estres")
    c.on_connect = _al_conectar
    c.on_message = _al_mensaje
    c.connect_async(MQTT_HOST, MQTT_PORT, keepalive=30)
    c.loop_start()
    return c


def enviar_al_esp32(cliente, comando: str, evento_esperado: str):
    """Publica un comando y espera la confirmacion del ESP32. Devuelve el dict del evento o None."""
    while not eventos.empty():
        eventos.get_nowait()                 # descarta confirmaciones viejas
    info = cliente.publish(TOPIC_COMANDOS, comando)
    limite = time.time() + ESPERA_ESP32_S
    while time.time() < limite:
        try:
            ev = eventos.get(timeout=0.5)
        except queue.Empty:
            continue
        if ev.get("evento") == evento_esperado:
            return ev
    return None


# ----------------------------------------------------------------------
# 3. API (FastAPI en Render) -> base de datos
# ----------------------------------------------------------------------
_token = None


def _login():
    global _token
    r = requests.post(API_BASE + "/auth/login", json={"email": BOT_EMAIL, "password": BOT_PASSWORD}, timeout=90)
    r.raise_for_status()
    _token = r.json()["access_token"]


def api_get(ruta: str):
    """GET autenticado con JWT; reintenta una vez si el token expiro."""
    global _token
    if not _token:
        _login()
    for intento in (1, 2):
        r = requests.get(API_BASE + ruta, headers={"Authorization": "Bearer " + _token}, timeout=90)
        if r.status_code == 401 and intento == 1:
            _login()
            continue
        r.raise_for_status()
        return r.json()


def clasificar(temp: float, hum: float) -> str:
    # Mismos umbrales del firmware y de la app.
    if hum < 15 or temp > 40:
        return "crítico"
    if hum < 30 or temp > 35:
        return "estrés"
    if hum < 50 or temp > 28:
        return "precaución"
    return "óptimo"


def texto_ultimo_registro() -> str:
    filas = api_get("/estadisticas/ultimo-registro")
    t = next((f for f in filas if "temp" in f["tipo_medicion"]), None)
    h = next((f for f in filas if "hum" in f["tipo_medicion"]), None)
    if not t or not h:
        return "Todavía no hay registros guardados en la base de datos."
    return (f"🗄️ Último registro guardado (zona {h['id_zona']}, {str(h['fecha_hora'])[:16].replace('T', ' ')}):\n"
            f"• Humedad: {float(h['valor']):.1f} %\n• Temperatura: {float(t['valor']):.1f} °C\n"
            f"• Estado: {clasificar(float(t['valor']), float(h['valor']))}")


def texto_promedio_24h() -> str:
    filas = api_get("/estadisticas/promedio-24h")
    if not filas:
        return "No hay datos para calcular el promedio de 24 horas."
    t = next((f for f in filas if "temp" in f["tipo_medicion"]), None)
    h = next((f for f in filas if "hum" in f["tipo_medicion"]), None)
    partes = ["📊 Promedio de las últimas 24 horas con datos:"]
    if h:
        partes.append(f"• Humedad: {float(h['promedio']):.1f} % ({h['registros']} registros)")
    if t:
        partes.append(f"• Temperatura: {float(t['promedio']):.1f} °C ({t['registros']} registros)")
    return "\n".join(partes)


def texto_resumen_dia() -> str:
    filas = api_get("/estadisticas/resumen-dia")
    if not filas:
        return "No hay mediciones para armar el resumen del día."
    partes = [f"📈 Máximos y mínimos del día {str(filas[0]['fecha'])[:10]}:"]
    for f in filas:
        es_temp = "temp" in f["tipo_medicion"]
        u = "°C" if es_temp else "%"
        partes.append(f"• {'Temperatura' if es_temp else 'Humedad'}: máx {float(f['maximo']):.1f} {u} · "
                      f"mín {float(f['minimo']):.1f} {u} · prom {float(f['promedio']):.1f} {u}")
    return "\n".join(partes)


def texto_distribucion_estados() -> str:
    filas = api_get("/estadisticas/distribucion-estados")
    if not filas:
        return "Todavía no hay mediciones suficientes para calcular los estados."
    orden = ["optimo", "precaucion", "estres", "critico"]
    nombres = {"optimo": "🟢 Óptimo", "precaucion": "🟡 Precaución", "estres": "🟠 Estrés", "critico": "🔴 Crítico"}
    por_estado = {f["estado"]: f for f in filas}
    total = sum(int(f["muestras"]) for f in filas)
    partes = [f"📊 Estado del suelo en el historial ({total} muestras):"]
    for k in orden:
        f = por_estado.get(k)
        partes.append(f"• {nombres[k]}: {float(f['porcentaje']):.1f} % ({f['muestras']})" if f else f"• {nombres[k]}: 0 %")
    dominante = max(filas, key=lambda f: int(f["muestras"]))["estado"]
    partes.append(f"Predomina el estado {dominante.replace('optimo', 'óptimo').replace('precaucion', 'precaución').replace('estres', 'estrés').replace('critico', 'crítico')}.")
    return "\n".join(partes)


CONSEJO_FIJO = {
    "óptimo": "El suelo está bien. No hace falta regar ahora; revisa de nuevo más tarde.",
    "precaución": "El suelo está en el límite. Conviene programar un riego pronto.",
    "estrés": "Hay estrés hídrico. Riega hoy y vuelve a medir después.",
    "crítico": "Condición crítica. Riega de inmediato.",
}


def texto_recomendacion() -> str:
    """Toma el ultimo registro de la API y pide al LLM un consejo corto basado SOLO en esos datos."""
    filas = api_get("/estadisticas/ultimo-registro")
    t = next((f for f in filas if "temp" in f["tipo_medicion"]), None)
    h = next((f for f in filas if "hum" in f["tipo_medicion"]), None)
    if not t or not h:
        return "No hay registros para recomendar. Revisa que el sensor esté enviando datos."
    temp, hum = float(t["valor"]), float(h["valor"])
    estado = clasificar(temp, hum)
    datos = f"Humedad del suelo: {hum:.1f} %. Temperatura del suelo: {temp:.1f} °C. Estado: {estado}."
    try:
        r = requests.post(OLLAMA_URL + "/api/chat", json={
            "model": OLLAMA_MODEL, "stream": False, "options": {"temperature": 0.3},
            "messages": [
                {"role": "system", "content": "Eres un asistente agrónomo. Con SOLO los datos que te dan, "
                 "escribe una recomendación de riego en máximo 3 frases cortas, en español. Umbrales del sistema: "
                 "óptimo (humedad >= 50 % y temp <= 28 °C), precaución, estrés (humedad < 30 % o temp > 35 °C), "
                 "crítico (humedad < 15 % o temp > 40 °C). No inventes datos ni cantidades de agua."},
                {"role": "user", "content": datos}]}, timeout=120)
        r.raise_for_status()
        consejo = r.json()["message"]["content"].strip()
    except Exception as e:
        print("   Ollama falló en recomendación:", e)
        consejo = CONSEJO_FIJO[estado]
    return f"🌱 Zona {h['id_zona']} · humedad {hum:.1f} % · temp {temp:.1f} °C · estado {estado}\n\n{consejo}"


# ----------------------------------------------------------------------
# 4. Acciones por intencion
# ----------------------------------------------------------------------
AYUDA = ("Soy el bot del sistema de estrés hídrico. Puedes escribirme con tus palabras, por ejemplo:\n"
         "💡 “enciende el LED” / “apaga la luz”\n"
         "🌡️ “¿cómo está la humedad ahora?” (lectura en vivo del ESP32)\n"
         "🗄️ “muéstrame el último registro” (dato guardado en la base)\n"
         "📊 “dame el promedio de las últimas 24 horas”\n"
         "📈 “¿cuál fue la humedad más alta y más baja de hoy?”\n"
         "📊 “¿cómo ha estado el suelo en general?”\n"
         "🌱 “¿debería regar hoy?” (consejo generado por el modelo)")


ACENTOS = {"optimo": "óptimo", "precaucion": "precaución", "estres": "estrés", "critico": "crítico"}


def ejecutar(intent: str, mqtt_cliente) -> str:
    if intent == "encender_led" or intent == "apagar_led":
        quiere_on = intent == "encender_led"
        ev = enviar_al_esp32(mqtt_cliente, intent, "led")
        if ev is None:
            return "⚠️ Envié la orden, pero el ESP32 no confirmó. ¿Está encendido y conectado al WiFi y al broker MQTT?"
        on = ev.get("estado") == "on"
        if on != quiere_on:
            return "⚠️ El ESP32 respondió con un estado inesperado."
        return ("💡 LED encendido ✅" if on else "🌑 LED apagado ✅") + " (confirmado por el ESP32)"
    if intent == "leer_sensor":
        ev = enviar_al_esp32(mqtt_cliente, "leer_sensor", "sensor")
        if ev is None:
            try:
                resp = texto_ultimo_registro()
            except Exception:
                resp = "Tampoco pude consultar la base de datos."
            return "⚠️ El ESP32 no respondió en vivo. Te muestro lo último guardado:\n" + resp
        return (f"🌡️ Lectura en vivo (zona {ev.get('id_zona')}):\n• Humedad: {ev.get('hum')} %\n"
                f"• Temperatura: {float(ev.get('temp')):.1f} °C\n• Estado: {ACENTOS.get(str(ev.get('estado', '')).lower(), '')}")
    if intent == "ultimo_registro":
        return texto_ultimo_registro()
    if intent == "promedio_24h":
        return texto_promedio_24h()
    if intent == "resumen_dia":
        return texto_resumen_dia()
    if intent == "distribucion_estados":
        return texto_distribucion_estados()
    if intent == "recomendar_riego":
        return texto_recomendacion()
    if intent == "ayuda":
        return AYUDA
    return ("No entendí esa orden 🤔. Puedo encender o apagar el LED, leer los sensores, mostrar "
            "registros, promedios, máximos y mínimos, el historial de estados y recomendar riego. Escribe “ayuda” para ver ejemplos.")


# ----------------------------------------------------------------------
# 5. Telegram (long polling)
# ----------------------------------------------------------------------
def tg(metodo: str, **params):
    r = requests.post(f"{TELEGRAM_API}/bot{TELEGRAM_TOKEN}/{metodo}", json=params, timeout=70)
    r.raise_for_status()
    return r.json()


def procesar(chat_id: int, texto: str, mqtt_cliente):
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        tg("sendMessage", chat_id=chat_id, text="No estás autorizado para usar este bot.")
        return
    tg("sendChatAction", chat_id=chat_id, action="typing")
    inicio = time.time()
    aviso = ""
    if texto.strip().lower() in ("/start", "/ayuda", "/help"):
        intent, origen = "ayuda", "comando"
    else:
        try:
            intent = detectar_intencion_llm(texto)
            origen = "LLM"
        except Exception as e:
            intent = detectar_intencion_reglas(texto)
            origen = "reglas"
            aviso = "\n\n(ℹ️ El modelo local no respondió; interpreté tu mensaje con reglas simples.)"
            print("   Ollama falló:", e)
    print(f"[{chat_id}] {texto!r} -> {intent} ({origen}, {time.time() - inicio:.1f}s)")
    try:
        respuesta = ejecutar(intent, mqtt_cliente)
    except Exception as e:
        print("   error ejecutando:", e)
        respuesta = "Ocurrió un error al ejecutar la orden. Intenta de nuevo en un momento."
    tg("sendMessage", chat_id=chat_id, text=respuesta + aviso)


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN en el archivo .env (créalo con @BotFather).")
    print("Bot iniciado. Modelo:", OLLAMA_MODEL, "| MQTT:", f"{MQTT_HOST}:{MQTT_PORT}", "| API:", API_BASE)
    mqtt_cliente = crear_cliente_mqtt()
    offset = None
    while True:
        try:
            datos = tg("getUpdates", timeout=30, offset=offset)
        except Exception as e:
            print("Error de red con Telegram:", e)
            time.sleep(3)
            continue
        for u in datos.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            if msg.get("text"):
                procesar(msg["chat"]["id"], msg["text"], mqtt_cliente)


if __name__ == "__main__":
    main()
