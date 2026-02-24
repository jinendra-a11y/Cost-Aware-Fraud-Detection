from nicegui import ui, events
import requests
import json
import asyncio
import websockets
from PIL import Image

API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

uploaded_files = []
upload_status = {'to_upload': 0, 'uploaded': 0}
# ---------------- Handlers & Logic ----------------
def handle_added(e):
    # e.args is a list of files added
    upload_status['to_upload'] += len(e.args)

# 3. Process each individual file
async def handle_single_upload(e: events.UploadEventArguments):
    file_bytes = await e.file.read()
    uploaded_files.append({"name": e.file.name, "content": file_bytes})
    
    # Increment finished count
    upload_status['uploaded'] += 1
    
    # Check if we are done
    if upload_status['uploaded'] >= upload_status['to_upload']:
        ui.notify(f"Success: {upload_status['uploaded']} files attached!", color='positive')
        # Reset for next batch
        upload_status['to_upload'] = 0
        upload_status['uploaded'] = 0

# ---------------- UI Styling & Layout ----------------
ui.query('body').style('font-family: Inter, sans-serif; background-color: #f8fafc;')

with ui.card().classes('w-full max-w-2xl mx-auto mt-10 p-6 shadow-lg'):
    ui.label("💳 Expense Approval Pipeline").classes('text-3xl font-bold text-slate-800 mb-4')
    
    with ui.row().classes('w-full items-center'):
        job_id_input = ui.input("Job ID").classes('flex-1')
        vehicle = ui.select(["Fuel", "EV", "Hybrid"], value="Fuel", label="Vehicle Type").classes('w-40')

    with ui.row().classes('w-full'):
        pickup = ui.input("Pickup Postal Code").classes('flex-1')
        drop = ui.input("Drop Postal Code").classes('flex-1')

    with ui.row().classes('w-full'):
        pickup_time = ui.input("Pickup Time").props('type="datetime-local"').classes('flex-1')
        drop_time = ui.input("Drop Time").props('type="datetime-local"').classes('flex-1')
    
    # Radio buttons for mode selection
    with ui.row().classes('w-full mt-2'):
        with ui.column().classes('flex-1'):
            ui.label("Execution Mode").classes('text-sm font-medium text-slate-700')
            environment_mode = ui.radio(
                ["DEBUG", "PRODUCTION"],
                value="DEBUG"
            ).props('inline')

    upload_ui = ui.upload(
    label="Upload Bill Images",
    multiple=True,
    on_upload=handle_single_upload,
).on('added', handle_added).classes('w-full mt-4')

    submit_btn = ui.button("Run Fraud Detection", on_click=lambda: submit_job()).classes('w-full mt-4 py-3')
    
    with ui.column().classes('w-full mt-6 p-4 bg-white border rounded-lg'):
        with ui.row().classes('items-center gap-2'):
            spinner = ui.spinner(size='sm')
            spinner.set_visibility(False) # Start hidden
            status = ui.label("Status: Idle").classes('font-medium text-slate-600')
        
        progress_text = ui.label("Progress: 0%").classes('text-xs text-slate-500 mt-2')
        progress_bar = ui.linear_progress(value=0).classes('mt-1')

# ---------------- Helper Functions ----------------
def resize_with_padding(image_path, size=(500, 500)):
    img = Image.open(image_path).convert("RGB")
    # Maintain aspect ratio
    img.thumbnail(size, Image.LANCZOS)
    # Create white background
    new_img = Image.new("RGB", size, (255, 255, 255))
    # Center the image
    paste_x = (size[0] - img.size[0]) // 2
    paste_y = (size[1] - img.size[1]) // 2

    new_img.paste(img, (paste_x, paste_y))

    new_path = image_path 
    new_img.save(new_path, quality=95)
    return new_path

def show_results(data, client):
    """Results popup with parallel layout (Left: Image, Right: Bill Info)."""

    bills = data.get("result", [])

    with client:
        with ui.dialog() as dialog, ui.card().classes('w-11/12 max-w-6xl'):
            ui.label("💼 Fraud Detection Results") \
                .classes("text-2xl font-bold text-slate-800 mb-4")
            
            with ui.scroll_area().style('height: 520px; width: 100%'):
                if not bills:
                    ui.label("No data found in processed bills.") \
                        .classes("text-slate-500 italic")
                else:
                    for bill in bills:
                        image_path = bill.get("bill_id")

                        # 🔹 Main Card
                        with ui.card().classes("m-4 p-4 bg-slate-50 rounded-xl shadow-md"):
                            # 🔥 Parallel Layout Row
                            with ui.row().classes("w-full gap-6 items-start flex-nowrap"):
                                # ---------------- LEFT SIDE (IMAGE) ----------------
                                with ui.column().style("width: 520px; flex-shrink: 0;"):
                                    if image_path:
                                        fixed_image = resize_with_padding(image_path)

                                        ui.image(fixed_image).style("""width: 500px; height: 500px;""")

                                # ---------------- RIGHT SIDE (BILL INFO) ----------------
                                with ui.column().classes("flex-1"):

                                    ui.label("Bill Information") \
                                        .classes("text-lg font-semibold mb-2")

                                    formatted_json = json.dumps(bill, indent=2, ensure_ascii=False)

                                    ui.markdown(f"```json\n{formatted_json}\n```").classes("w-full text-sm")


            ui.button("Close", on_click=dialog.close) \
                .classes("mt-4 w-full bg-slate-800 text-white")

        dialog.open()


async def listen_ws_async(job_id_value, client):
    uri = f"{WS_URL}/job/{job_id_value}/"
    try:
        async with websockets.connect(uri) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)

                with client:
                    current_status = data.get("status", "PROCESSING")
                    status.set_text(f"Status: {current_status}")
                    
                    prog = data.get("progress", 0)
                    progress_bar.set_value(prog / 100)
                    progress_text.set_text(f"Progress: {prog}%")

                    if current_status in ("COMPLETED", "FAILED"):
                        spinner.set_visibility(False)
                        show_results(data, client)
                        break

    except Exception as e:
        with client:
            spinner.set_visibility(False)
            ui.notify(f"Connection Lost: {e}", type='negative')

def submit_job():
    if not uploaded_files:
        ui.notify("Please upload at least one image.", type='warning')
        return
    if not job_id_input.value:
        ui.notify("Job ID is required.", type='warning')
        return

    files = [("files", (f["name"], f["content"], "application/octet-stream")) for f in uploaded_files]
    payload = {
        "job_id": job_id_input.value,
        "pickup_location": pickup.value,
        "drop_location": drop.value,
        "pickup_time": pickup_time.value,
        "drop_time": drop_time.value,
        "vehicle_type": vehicle.value,
    }

    try:
        r = requests.post(
            f"{API_URL}/api/jobs/submit-job",
            data={"job_details": json.dumps(payload), "mode": environment_mode.value},
            files=files,
            timeout=5
        )
        
        if r.status_code == 200:
            status.set_text("Connecting to stream...")
            spinner.set_visibility(True)
            
            client = ui.context.client
            asyncio.create_task(listen_ws_async(job_id_input.value, client))
        else:
            ui.notify(f"Submission Error: {r.status_code}", type='negative')
    except Exception as e:
        ui.notify(f"Backend unreachable: {e}", type='negative')

ui.run(title="Expense Approval Pipeline", port=8080, host="0.0.0.0", reload=False)