# Kachicinema

[![Open Source](https://img.shields.io/badge/open%20source-yes-2ea44f.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-web%20server-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Cloudflare Tunnel](https://img.shields.io/badge/Cloudflare-Tunnel-F38020.svg?logo=cloudflare&logoColor=white)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

> Servidor local pequeno para publicar un video mediante una URL temporal o un dominio propio de Cloudflare Tunnel.

## Que hace

La aplicacion:

- Busca el primer archivo `.mp4` dentro de `movies/`.
- Lo sirve en `http://127.0.0.1:5000/video.mp4`.
- Acepta solicitudes HTTP `Range`, necesarias para que los reproductores puedan avanzar, pausar y descargar el video por partes.
- Inicia automaticamente un Cloudflare Quick Tunnel si no se configura un Named Tunnel.
- Muestra en la terminal la URL publica generada.

El servidor no incluye una interfaz web ni un sistema de autenticacion. La URL publica debe tratarse como temporal y compartirse con cuidado.

## Requisitos

- Python 3.10 o superior.
- `cloudflared` instalado y disponible en el `PATH` para poder crear el tunel.
- Un archivo `.mp4` dentro de `movies/`.

## Instalacion

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install flask
```

Instala tambien `cloudflared` siguiendo la documentacion oficial de Cloudflare:

<https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/>

Despues, crea la carpeta `movies/` si no existe y coloca dentro el video que quieras publicar.

## Uso rapido: Quick Tunnel

Este modo es el predeterminado:

```powershell
python main.py
```

La aplicacion iniciara Flask en el puerto local `5000` y tratara de crear una URL parecida a:

```text
https://algo-aleatorio.trycloudflare.com/video.mp4
```

Un Quick Tunnel es temporal y normalmente no requiere iniciar sesion en una cuenta de Cloudflare. Si `cloudflared` no esta instalado, no esta en el `PATH` o no puede conectarse con Cloudflare, la aplicacion terminara con un error.

## Uso con Named Tunnel

Para usar un dominio propio, primero configura y autentica `cloudflared` con Cloudflare. La sesion o credenciales activas son necesarias para administrar o ejecutar un tunel nombrado; no son un requisito general de Flask ni del puerto `5000`.

Define estas variables antes de iniciar la aplicacion:

```powershell
$env:CF_TUNNEL_NAME = "mi-tunel"
$env:CF_HOSTNAME = "video.ejemplo.com"
python main.py
```

`CF_TUNNEL_NAME` debe coincidir con el tunel creado en Cloudflare y `CF_HOSTNAME` debe apuntar al hostname configurado para ese tunel. La aplicacion ejecuta:

```text
cloudflared tunnel run mi-tunel --no-autoupdate
```

Consulta la guia oficial para crear el tunel y enrutar el DNS:

<https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/>

## Problemas frecuentes

### “No se pudo iniciar Cloudflare Tunnel”

Comprueba lo siguiente:

1. Ejecuta `cloudflared --version` y confirma que el comando funciona.
2. Verifica que `cloudflared` esta en el `PATH`, o instala la version oficial para Windows.
3. Para un Named Tunnel, confirma que el nombre, las credenciales y el hostname estan configurados.
4. Comprueba que la red o el firewall permiten la conexion saliente de `cloudflared`.

### La URL funciona pero el video no carga o no avanza

Verifica que exista al menos un `.mp4` directamente dentro de `movies/` y que el archivo no este siendo modificado mientras se reproduce. Tambien puedes probar la URL exacta `/video.mp4` en lugar de la raiz del dominio.

El cache puede mostrar una respuesta anterior, pero no es la causa principal de que una sesion de Cloudflare sea necesaria: la autenticacion afecta al acceso al Named Tunnel, mientras que el Quick Tunnel depende de que `cloudflared` consiga conectarse y mantener el proceso activo.

## Estructura

```text
Kachicinema/
|-- main.py
|-- movies/
|   `-- tu-video.mp4
|-- LICENSE
`-- README.md
```

## Licencia

Este proyecto se distribuye bajo la licencia personalizada incluida en [LICENSE](LICENSE). Permite usar, copiar, modificar, fusionar, publicar y distribuir el proyecto para cualquier fin. La atribucion a `@ItsKachi_VT` se agradece cuando se use con fines comerciales, se obtenga beneficio economico o se incorporen mejoras significativas, pero es opcional.

Consulta el archivo [LICENSE](LICENSE) para el texto completo y las condiciones de responsabilidad.