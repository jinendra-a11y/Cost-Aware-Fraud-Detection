# from nicegui import ui, events
# import requests
# import json
# import asyncio
# import websockets
# from PIL import Image

# API_URL = "http://127.0.0.1:8000"
# WS_URL = "ws://127.0.0.1:8000/ws"

# uploaded_files = []
# upload_status = {'to_upload': 0, 'uploaded': 0}

# # ============================================================================
# # HELPER FUNCTIONS (JOB SUBMISSION TAB)
# # ============================================================================

# def handle_added(e):
#     """Handle when files are added to upload widget."""
#     upload_status['to_upload'] += len(e.args)

# async def handle_single_upload(e: events.UploadEventArguments):
#     """Process each individual file upload."""
#     file_bytes = await e.file.read()
#     uploaded_files.append({"name": e.file.name, "content": file_bytes})
    
#     upload_status['uploaded'] += 1
    
#     if upload_status['uploaded'] >= upload_status['to_upload']:
#         ui.notify(f"Success: {upload_status['uploaded']} files attached!", color='positive')
#         upload_status['to_upload'] = 0
#         upload_status['uploaded'] = 0

# def resize_with_padding(image_path, size=(500, 500)):
#     """Resize image with padding to maintain aspect ratio."""
#     img = Image.open(image_path).convert("RGB")
#     img.thumbnail(size, Image.LANCZOS)
#     new_img = Image.new("RGB", size, (255, 255, 255))
#     paste_x = (size[0] - img.size[0]) // 2
#     paste_y = (size[1] - img.size[1]) // 2
#     new_img.paste(img, (paste_x, paste_y))
#     new_path = image_path 
#     new_img.save(new_path, quality=95)
#     return new_path

# def show_results(data, client):
#     """Results popup with parallel layout (Left: Image, Right: Bill Info)."""
#     bills = data.get("result", [])

#     with client:
#         with ui.dialog() as dialog, ui.card().classes('w-11/12 max-w-6xl'):
#             ui.label("💼 Fraud Detection Results") \
#                 .classes("text-2xl font-bold text-slate-800 mb-4")
            
#             with ui.scroll_area().style('height: 520px; width: 100%'):
#                 if not bills:
#                     ui.label("No data found in processed bills.") \
#                         .classes("text-slate-500 italic")
#                 else:
#                     for bill in bills:
#                         image_path = bill.get("bill_id")

#                         # Main Card
#                         with ui.card().classes("m-4 p-4 bg-slate-50 rounded-xl shadow-md"):
#                             # Parallel Layout Row
#                             with ui.row().classes("w-full gap-6 items-start flex-nowrap"):
#                                 # LEFT SIDE (IMAGE)
#                                 with ui.column().style("width: 520px; flex-shrink: 0;"):
#                                     if image_path:
#                                         fixed_image = resize_with_padding(image_path)
#                                         ui.image(fixed_image).style("""width: 500px; height: 500px;""")

#                                 # RIGHT SIDE (BILL INFO)
#                                 with ui.column().classes("flex-1"):
#                                     ui.label("Bill Information") \
#                                         .classes("text-lg font-semibold mb-2")

#                                     formatted_json = json.dumps(bill, indent=2, ensure_ascii=False)
#                                     ui.markdown(f"```json\n{formatted_json}\n```").classes("w-full text-sm")

#             ui.button("Close", on_click=dialog.close) \
#                 .classes("mt-4 w-full bg-slate-800 text-white")

#         dialog.open()


# async def listen_ws_async(job_id_value, client):
#     """Listen to WebSocket updates for job progress."""
#     uri = f"{WS_URL}/job/{job_id_value}/"
#     try:
#         async with websockets.connect(uri) as ws:
#             while True:
#                 msg = await ws.recv()
#                 data = json.loads(msg)

#                 with client:
#                     current_status = data.get("status", "PROCESSING")
#                     status.set_text(f"Status: {current_status}")
                    
#                     prog = data.get("progress", 0)
#                     progress_bar.set_value(prog / 100)
#                     progress_text.set_text(f"Progress: {prog}%")

#                     if current_status in ("COMPLETED", "FAILED"):
#                         spinner.set_visibility(False)
#                         show_results(data, client)
#                         break

#     except Exception as e:
#         with client:
#             spinner.set_visibility(False)
#             ui.notify(f"Connection Lost: {e}", type='negative')

# def submit_job():
#     """Submit job with files to Django backend."""
#     if not uploaded_files:
#         ui.notify("Please upload at least one image.", type='warning')
#         return
#     if not job_id_input.value:
#         ui.notify("Job ID is required.", type='warning')
#         return

#     files = [("files", (f["name"], f["content"], "application/octet-stream")) for f in uploaded_files]
#     payload = {
#         "job_id": job_id_input.value,
#         "pickup_location": pickup.value,
#         "drop_location": drop.value,
#         "pickup_time": pickup_time.value,
#         "drop_time": drop_time.value,
#         "vehicle_type": vehicle.value,
#     }

#     try:
#         r = requests.post(
#             f"{API_URL}/api/jobs/submit-job",
#             data={"job_details": json.dumps(payload), "mode": environment_mode.value},
#             files=files,
#             timeout=5
#         )
        
#         if r.status_code == 200:
#             status.set_text("Connecting to stream...")
#             spinner.set_visibility(True)
            
#             client = ui.context.client
#             asyncio.create_task(listen_ws_async(job_id_input.value, client))
#         else:
#             ui.notify(f"Submission Error: {r.status_code}", type='negative')
#     except Exception as e:
#         ui.notify(f"Backend unreachable: {e}", type='negative')

# # ============================================================================
# # HELPER FUNCTIONS (ANALYTICS TAB)
# # ============================================================================

# def refresh_analytics():
#     """Fetch and refresh analytics data."""
#     try:
#         r = requests.get(f"{API_URL}/api/jobs/analytics/")
#         data = r.json()
        
#         groq_n = data.get("groq_normalization", {})
#         groq_f = data.get("groq_fraud", {})
#         gcv = data.get("google_vision", {})
#         combined = data.get("combined_total", "0")
#         per_job = data.get("per_job", [])
        
#         # Update Groq Normalization
#         groq_norm_calls.text = f"{groq_n.get('calls', 0)}"
#         groq_norm_tokens_in.text = f"{groq_n.get('tokens_in', 0):,}"
#         groq_norm_tokens_out.text = f"{groq_n.get('tokens_out', 0):,}"
#         groq_norm_cost.text = f"£{float(groq_n.get('total_cost', 0)):.4f}"
        
#         # Update Groq Fraud
#         groq_fraud_calls.text = f"{groq_f.get('calls', 0)}"
#         groq_fraud_tokens_in.text = f"{groq_f.get('tokens_in', 0):,}"
#         groq_fraud_tokens_out.text = f"{groq_f.get('tokens_out', 0):,}"
#         groq_fraud_cost.text = f"£{float(groq_f.get('total_cost', 0)):.4f}"
        
#         # Update Google Vision
#         gcv_calls.text = f"{gcv.get('calls', 0)}"
#         gcv_images.text = f"{gcv.get('images', 0):,}"
#         gcv_cost.text = f"£{float(gcv.get('total_cost', 0)):.4f}"
        
#         # Update Combined
#         combined_total.text = f"£{float(combined):.4f}"
        
#         # Update Per-Job Table
#         per_job_rows = []
#         for job in per_job:
#             per_job_rows.append({
#                 "job_id": job.get("job_id", "N/A"),
#                 "total_cost": f"£{float(job.get('job_total', 0)):.4f}",
#                 "created_at": job.get("created_at", "N/A")[:10] if job.get("created_at") else "N/A"
#             })
        
#         jobs_table.rows = per_job_rows
#         ui.notify("Analytics refreshed!", color='positive', position='top')
        
#     except Exception as e:
#         ui.notify(f"Failed to load analytics: {e}", type='negative')

# # ============================================================================
# # UI LAYOUT WITH TABS
# # ============================================================================

# ui.query('body').style('font-family: Inter, sans-serif; background-color: #f8fafc;')

# with ui.column().classes('w-full items-center'):

#     with ui.tabs().classes('w-full') as tabs:
#         ui.tab('Submit Job')
#         ui.tab('Analytics')

#     with ui.tab_panels(tabs, value='Submit Job'):

#         with ui.tab_panel("Submit Job"):
#             with ui.card().classes('w-full max-w-2xl mx-auto mt-10 p-6 shadow-lg'):
#                 ui.label("💳 Expense Approval Pipeline").classes('text-3xl font-bold text-slate-800 mb-4')
                
#                 with ui.row().classes('w-full items-center'):
#                     job_id_input = ui.input("Job ID").classes('flex-1')
#                     vehicle = ui.select(["Fuel", "EV", "Hybrid"], value="Fuel", label="Vehicle Type").classes('w-40')

#                 with ui.row().classes('w-full'):
#                     pickup = ui.input("Pickup Postal Code").classes('flex-1')
#                     drop = ui.input("Drop Postal Code").classes('flex-1')

#                 with ui.row().classes('w-full'):
#                     pickup_time = ui.input("Pickup Time").props('type="datetime-local"').classes('flex-1')
#                     drop_time = ui.input("Drop Time").props('type="datetime-local"').classes('flex-1')
                
#                 # Radio buttons for mode selection
#                 with ui.row().classes('w-full mt-2'):
#                     with ui.column().classes('flex-1'):
#                         ui.label("Execution Mode").classes('text-sm font-medium text-slate-700')
#                         environment_mode = ui.radio(
#                             ["DEBUG", "PRODUCTION"],
#                             value="DEBUG"
#                         ).props('inline')

#                 upload_ui = ui.upload(
#                     label="Upload Bill Images",
#                     multiple=True,
#                     on_upload=handle_single_upload,
#                 ).on('added', handle_added).classes('w-full mt-4')

#                 submit_btn = ui.button("Run Fraud Detection", on_click=lambda: submit_job()).classes('w-full mt-4 py-3')
                
#                 with ui.column().classes('w-full mt-6 p-4 bg-white border rounded-lg'):
#                     with ui.row().classes('items-center gap-2'):
#                         spinner = ui.spinner(size='sm')
#                         spinner.set_visibility(False)
#                         status = ui.label("Status: Idle").classes('font-medium text-slate-600')
                    
#                     progress_text = ui.label("Progress: 0%").classes('text-xs text-slate-500 mt-2')
#                     progress_bar = ui.linear_progress(value=0).classes('mt-1')

#             # ========== TAB 2: ANALYTICS ==========
#         with ui.tab_panel("Analytics"):
#             with ui.column().classes('w-full max-w-6xl mx-auto mt-10 p-6'):
#                 ui.label("📊 LLM Analytics Dashboard").classes('text-3xl font-bold text-slate-800 mb-2')
                
#                 with ui.row().classes('w-full gap-2 mb-6'):
#                     ui.button("Refresh Analytics", on_click=refresh_analytics) \
#                         .classes('px-4 py-2 bg-blue-600 text-white rounded')
                
#                 # Groq Normalization Card
#                 with ui.card().classes('w-full mb-4'):
#                     ui.label("🚀 Groq Normalization (llama-3.1-8b-instant)") \
#                         .classes('text-lg font-bold text-slate-800 mb-4')
                    
#                     with ui.grid(columns=4).classes('w-full gap-4'):
#                         with ui.column():
#                             ui.label("API Calls").classes('text-sm text-slate-600 font-medium')
#                             groq_norm_calls = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Input Tokens").classes('text-sm text-slate-600 font-medium')
#                             groq_norm_tokens_in = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Output Tokens").classes('text-sm text-slate-600 font-medium')
#                             groq_norm_tokens_out = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Total Cost").classes('text-sm text-slate-600 font-medium')
#                             groq_norm_cost = ui.label("£0.0000").classes('text-2xl font-bold text-green-600')

#                 # Groq Fraud Card
#                 with ui.card().classes('w-full mb-4'):
#                     ui.label("🔍 Groq Fraud Detection (llama-3.3-70b-versatile)") \
#                         .classes('text-lg font-bold text-slate-800 mb-4')
                    
#                     with ui.grid(columns=4).classes('w-full gap-4'):
#                         with ui.column():
#                             ui.label("API Calls").classes('text-sm text-slate-600 font-medium')
#                             groq_fraud_calls = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Input Tokens").classes('text-sm text-slate-600 font-medium')
#                             groq_fraud_tokens_in = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Output Tokens").classes('text-sm text-slate-600 font-medium')
#                             groq_fraud_tokens_out = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Total Cost").classes('text-sm text-slate-600 font-medium')
#                             groq_fraud_cost = ui.label("£0.0000").classes('text-2xl font-bold text-red-600')

#                 # Google Vision Card
#                 with ui.card().classes('w-full mb-4'):
#                     ui.label("📸 Google Vision OCR").classes('text-lg font-bold text-slate-800 mb-4')
                    
#                     with ui.grid(columns=3).classes('w-full gap-4'):
#                         with ui.column():
#                             ui.label("API Calls").classes('text-sm text-slate-600 font-medium')
#                             gcv_calls = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Images Processed").classes('text-sm text-slate-600 font-medium')
#                             gcv_images = ui.label("0").classes('text-2xl font-bold text-slate-800')
                        
#                         with ui.column():
#                             ui.label("Total Cost").classes('text-sm text-slate-600 font-medium')
#                             gcv_cost = ui.label("£0.0000").classes('text-2xl font-bold text-blue-600')

#                 # Combined Cost
#                 with ui.card().classes('w-full mb-4 bg-gradient-to-r from-slate-100 to-slate-200'):
#                     with ui.row().classes('w-full items-center justify-between'):
#                         ui.label("💰 Combined Total Cost").classes('text-lg font-bold text-slate-800')
#                         combined_total = ui.label("£0.0000").classes('text-3xl font-bold text-slate-900')

#                 # Per-Job Cost Table
#                 with ui.card().classes('w-full'):
#                     ui.label("📋 Cost by Job (Last 10)").classes('text-lg font-bold text-slate-800 mb-4')
                    
#                     jobs_table = ui.table(columns=[
#                         {'name': 'job_id', 'label': 'Job ID', 'field': 'job_id'},
#                         {'name': 'total_cost', 'label': 'Total Cost', 'field': 'total_cost'},
#                         {'name': 'created_at', 'label': 'Created At', 'field': 'created_at'},
#                     ], rows=[]).classes('w-full')


# ui.run(title="Expense AI Dashboard", port=8080)



from nicegui import ui, events
import requests
import json
import asyncio
import websockets
import os
from PIL import Image

BACKEND_URL = os.getenv("BACKEND_URL")
API_URL = BACKEND_URL + "/api"
WS_URL = BACKEND_URL + "/ws"

uploaded_files = []
upload_status = {'to_upload': 0, 'uploaded': 0}

# ============================================================================
# HELPER FUNCTIONS (JOB SUBMISSION TAB)
# ============================================================================

def handle_added(e):
    upload_status['to_upload'] += len(e.args)

async def handle_single_upload(e: events.UploadEventArguments):
    file_bytes = await e.file.read()
    uploaded_files.append({"name": e.file.name, "content": file_bytes})
    upload_status['uploaded'] += 1
    if upload_status['uploaded'] >= upload_status['to_upload']:
        ui.notify(f"✓ {upload_status['uploaded']} files attached", color='positive', position='top-right')
        upload_status['to_upload'] = 0
        upload_status['uploaded'] = 0

def resize_with_padding(image_path, size=(500, 500)):
    img = Image.open(image_path).convert("RGB")
    img.thumbnail(size, Image.LANCZOS)
    new_img = Image.new("RGB", size, (255, 255, 255))
    paste_x = (size[0] - img.size[0]) // 2
    paste_y = (size[1] - img.size[1]) // 2
    new_img.paste(img, (paste_x, paste_y))
    new_img.save(image_path, quality=95)
    return image_path

def show_results(data, client):
    bills = data.get("result", [])
    with client:
        with ui.dialog() as dialog, ui.card().classes('w-11/12 max-w-6xl').style('background: #ffffff; border-radius: 16px; box-shadow: 0 25px 60px rgba(0,0,0,0.15);'):
            with ui.row().classes('w-full items-center justify-between').style('padding: 20px 24px 16px; border-bottom: 1px solid #f1f5f9;'):
                with ui.row().classes('items-center gap-3'):
                    with ui.element('div').style('width: 40px; height: 40px; background: linear-gradient(135deg, #eef2ff, #e0e7ff); border-radius: 10px; display: flex; align-items: center; justify-content: center;'):
                        ui.label('🔍').style('font-size: 18px;')
                    with ui.column().style('gap: 2px;'):
                        ui.label('Fraud Detection Results').style('font-family: "DM Sans", sans-serif; font-size: 18px; font-weight: 700; color: #0f172a;')
                        status_text = data.get("status", "COMPLETED")
                        status_color = '#22c55e' if status_text == 'COMPLETED' else '#ef4444'
                        ui.label(f'● {status_text}').style(f'font-size: 12px; font-weight: 600; color: {status_color};')
                ui.button(icon='close', on_click=dialog.close).props('flat round').style('color: #94a3b8;')

            with ui.scroll_area().style('height: 560px; width: 100%; padding: 16px 24px;'):
                if not bills:
                    with ui.column().classes('w-full items-center justify-center').style('padding: 60px 0;'):
                        ui.label('📭').style('font-size: 48px;')
                        ui.label('No data found in processed bills.').style('color: #94a3b8; font-family: "DM Sans", sans-serif; margin-top: 12px;')
                else:
                    for i, bill in enumerate(bills):
                        image_path = bill.get("bill_id")
                        with ui.card().style('background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 16px;'):
                            ui.label(f'Bill #{i+1}').style('font-size: 11px; font-weight: 700; color: #6366f1; background: #eef2ff; padding: 3px 10px; border-radius: 20px; display: inline-block; margin-bottom: 14px; letter-spacing: 0.05em;')
                            with ui.row().classes('w-full gap-6 items-start flex-nowrap'):
                                with ui.column().style('width: 520px; flex-shrink: 0;'):
                                    if image_path:
                                        fixed_image = resize_with_padding(image_path)
                                        ui.image(fixed_image).style('width: 500px; height: 500px; border-radius: 10px; border: 1px solid #e2e8f0;')
                                    else:
                                        with ui.element('div').style('width: 500px; height: 300px; background: #f1f5f9; border-radius: 10px; border: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: center;'):
                                            ui.label('No image').style('color: #94a3b8;')
                                with ui.column().classes('flex-1'):
                                    ui.label('BILL INFORMATION').style('font-size: 10px; font-weight: 700; color: #94a3b8; letter-spacing: 0.1em; margin-bottom: 12px;')
                                    formatted_json = json.dumps(bill, indent=2, ensure_ascii=False)
                                    ui.markdown(f"```json\n{formatted_json}\n```").classes('w-full text-sm')

            with ui.row().classes('w-full').style('padding: 16px 24px; border-top: 1px solid #f1f5f9;'):
                ui.button('Close', on_click=dialog.close).style('background: #0f172a; color: white; border-radius: 8px; font-family: "DM Sans", sans-serif; font-weight: 600; padding: 8px 24px;')
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
                    progress_text.set_text(f"{prog}% complete")
                    if current_status in ("COMPLETED", "FAILED"):
                        spinner.set_visibility(False)
                        show_results(data, client)
                        break
    except Exception as e:
        with client:
            spinner.set_visibility(False)
            ui.notify(f"Connection lost: {e}", type='negative', position='top-right')

def submit_job():
    if not uploaded_files:
        ui.notify("Please upload at least one image.", type='warning', position='top-right')
        return
    if not job_id_input.value:
        ui.notify("Job ID is required.", type='warning', position='top-right')
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
            ui.notify(f"Submission error: {r.status_code}", type='negative', position='top-right')
    except Exception as e:
        ui.notify(f"Backend unreachable: {e}", type='negative', position='top-right')

# ============================================================================
# HELPER FUNCTIONS (ANALYTICS TAB)
# ============================================================================

def refresh_analytics():
    try:
        r = requests.get(f"{API_URL}/api/jobs/analytics/")
        data = r.json()
        groq_n = data.get("groq_normalization", {})
        groq_f = data.get("groq_fraud", {})
        gcv = data.get("google_vision", {})
        combined = data.get("combined_total", "0")
        per_job = data.get("per_job", [])
        groq_norm_calls.text = f"{groq_n.get('calls', 0)}"
        groq_norm_tokens_in.text = f"{groq_n.get('tokens_in', 0):,}"
        groq_norm_tokens_out.text = f"{groq_n.get('tokens_out', 0):,}"
        groq_norm_cost.text = f"£{float(groq_n.get('total_cost', 0)):.4f}"
        groq_fraud_calls.text = f"{groq_f.get('calls', 0)}"
        groq_fraud_tokens_in.text = f"{groq_f.get('tokens_in', 0):,}"
        groq_fraud_tokens_out.text = f"{groq_f.get('tokens_out', 0):,}"
        groq_fraud_cost.text = f"£{float(groq_f.get('total_cost', 0)):.4f}"
        gcv_calls.text = f"{gcv.get('calls', 0)}"
        gcv_images.text = f"{gcv.get('images', 0):,}"
        gcv_cost.text = f"£{float(gcv.get('total_cost', 0)):.4f}"
        combined_total.text = f"£{float(combined):.4f}"
        per_job_rows = []
        for job in per_job:
            per_job_rows.append({
                "job_id": job.get("job_id", "N/A"),
                "total_cost": f"£{float(job.get('job_total', 0)):.4f}",
                "created_at": job.get("created_at", "N/A")[:10] if job.get("created_at") else "N/A"
            })
        jobs_table.rows = per_job_rows
        ui.notify("Analytics refreshed", color='positive', position='top-right')
    except Exception as e:
        ui.notify(f"Failed to load analytics: {e}", type='negative', position='top-right')

# ============================================================================
# GLOBAL STYLES — LIGHT / DAY MODE
# ============================================================================

ui.add_head_html('''
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; }

  body, .q-page, .nicegui-content, html {
    background: #f8fafc !important;
    font-family: "DM Sans", sans-serif !important;
    color: #0f172a !important;
  }

  .app-header {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .q-tabs {
    background: #ffffff !important;
    border-bottom: 1px solid #e2e8f0 !important;
  }
  .q-tab {
    color: #94a3b8 !important;
    font-family: "DM Sans", sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    padding: 12px 32px !important;
    min-height: 48px !important;
  }
  .q-tab--active { color: #6366f1 !important; }
  .q-tab__indicator { background: #6366f1 !important; height: 2px !important; }
  .q-tab-panels { background: transparent !important; }
  .q-tab-panel { padding: 0 !important; }

  .q-card {
    background: #ffffff !important;
    border-radius: 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04) !important;
  }

  .q-field__control {
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    transition: border-color 0.15s ease !important;
  }
  .q-field__native, .q-field__input {
    color: #0f172a !important;
    font-family: "DM Sans", sans-serif !important;
    font-size: 14px !important;
  }
  .q-field__label {
    color: #94a3b8 !important;
    font-family: "DM Sans", sans-serif !important;
    font-size: 13px !important;
  }
  .q-field--focused .q-field__control { border-color: #6366f1 !important; background: #ffffff !important; }
  .q-field--focused .q-field__label { color: #6366f1 !important; }
  .q-select__dropdown-icon { color: #94a3b8 !important; }

  .main-btn .q-btn__content {
    font-family: "DM Sans", sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.02em !important;
  }
  .main-btn {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    transition: all 0.2s ease !important;
    color: #ffffff !important;
  }
  .main-btn:hover {
    box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
    transform: translateY(-1px) !important;
  }

  .refresh-btn {
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    color: #475569 !important;
    font-family: "DM Sans", sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: all 0.15s ease !important;
  }
  .refresh-btn:hover {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    background: #f5f3ff !important;
  }

  .q-uploader {
    background: #fafbff !important;
    border: 2px dashed #c7d2fe !important;
    border-radius: 12px !important;
    transition: border-color 0.2s ease !important;
  }
  .q-uploader:hover { border-color: #6366f1 !important; background: #f5f3ff !important; }
  .q-uploader__header { background: transparent !important; color: #6366f1 !important; }
  .q-uploader__header-content { color: #6366f1 !important; }
  .q-uploader__subtitle { color: #94a3b8 !important; font-size: 12px !important; }
  .q-uploader__list { background: transparent !important; }

  .q-linear-progress__track { background: #e2e8f0 !important; border-radius: 6px !important; }
  .q-linear-progress__model { background: linear-gradient(90deg, #6366f1, #818cf8) !important; border-radius: 6px !important; }

  .q-radio__bg { border-color: #cbd5e1 !important; }
  .q-radio__inner--truthy .q-radio__bg { border-color: #6366f1 !important; }
  .q-radio__check { background: #6366f1 !important; }
  .q-radio__label { color: #475569 !important; font-family: "DM Sans", sans-serif !important; font-size: 13px !important; font-weight: 500 !important; }

  .q-separator { background: #f1f5f9 !important; }
  .q-spinner { color: #6366f1 !important; }

  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: #f8fafc; }
  ::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 6px; }
  ::-webkit-scrollbar-thumb:hover { background: #cbd5e1; }

  .q-table { background: transparent !important; font-family: "DM Sans", sans-serif !important; }
  .q-table__container { box-shadow: none !important; }
  .q-table thead th {
    color: #94a3b8 !important; font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important;
    border-bottom: 1px solid #f1f5f9 !important; background: transparent !important;
    padding: 10px 16px !important;
  }
  .q-table tbody td {
    color: #475569 !important; font-size: 13px !important;
    border-bottom: 1px solid #f8fafc !important; padding: 12px 16px !important;
  }
  .q-table tbody tr:hover td { background: #f8fafc !important; }

  .q-notification { font-family: "DM Sans", sans-serif !important; border-radius: 10px !important; font-size: 13px !important; font-weight: 500 !important; }

  .q-menu { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important; }
  .q-item { color: #475569 !important; font-family: "DM Sans", sans-serif !important; font-size: 13px !important; }
  .q-item:hover, .q-item--active { background: #f5f3ff !important; color: #6366f1 !important; }

  pre {
    background: #f8fafc !important; border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important; padding: 14px !important;
    font-family: "DM Mono", monospace !important; font-size: 12px !important;
    color: #475569 !important; line-height: 1.6 !important;
  }
  code { font-family: "DM Mono", monospace !important; }

  .section-label {
    font-size: 10px !important; font-weight: 700 !important; color: #94a3b8 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    display: block; margin-bottom: 12px !important;
  }

  .stat-chip {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
  }
</style>
''')

# ============================================================================
# UI LAYOUT
# ============================================================================

with ui.column().classes('w-full').style('min-height: 100vh; background: #f8fafc;'):

    # ── Top Header Bar ──
    with ui.element('div').classes('app-header w-full'):
        with ui.row().classes('items-center gap-3'):
            with ui.element('div').style('width: 32px; height: 32px; background: linear-gradient(135deg, #6366f1, #818cf8); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;'):
                ui.label('⬡').style('color: white; font-size: 14px;')
            ui.label('ExpenseAI').style('font-size: 17px; font-weight: 700; color: #0f172a; letter-spacing: -0.02em;')
            ui.label('Fraud Detection Platform').style('font-size: 12px; color: #cbd5e1; margin-left: 2px; font-weight: 400;')

        with ui.row().classes('items-center gap-2'):
            with ui.element('div').style('width: 7px; height: 7px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 0 2px #dcfce7;'):
                pass
            ui.label('System Online').style('font-size: 12px; font-weight: 600; color: #64748b;')

    # ── Tab Navigation ──
    with ui.tabs().classes('w-full') as tabs:
        ui.tab('Submit Job', icon='send')
        ui.tab('Analytics', icon='bar_chart')

    with ui.tab_panels(tabs, value='Submit Job').style('background: transparent; flex: 1;'):

        # ============================================================
        # TAB 1 — SUBMIT JOB
        # ============================================================
        with ui.tab_panel('Submit Job').style('padding: 28px 36px;'):
            with ui.row().classes('w-full gap-6').style('max-width: 1200px; margin: 0 auto; align-items: flex-start;'):

                # ── LEFT: Form Card ──
                with ui.card().style('flex: 1; min-width: 420px; max-width: 560px; padding: 28px; border: 1px solid #e2e8f0;'):
                    with ui.row().classes('items-center gap-3').style('margin-bottom: 24px;'):
                        with ui.element('div').style('width: 40px; height: 40px; background: linear-gradient(135deg, #eef2ff, #e0e7ff); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;'):
                            ui.label('📋').style('font-size: 18px;')
                        with ui.column().style('gap: 2px;'):
                            ui.label('New Detection Job').style('font-size: 18px; font-weight: 700; color: #0f172a;')
                            ui.label('Fill in details and upload expense bills').style('font-size: 12px; color: #94a3b8;')

                    ui.label('Job Details').classes('section-label')
                    with ui.row().classes('w-full gap-3').style('margin-bottom: 16px;'):
                        job_id_input = ui.input('Job ID', placeholder='e.g. JOB-2024-001').classes('flex-1')
                        vehicle = ui.select(['Fuel', 'EV', 'Hybrid'], value='Fuel', label='Vehicle').style('width: 140px;')

                    ui.separator().style('margin: 16px 0;')

                    ui.label('Route Info').classes('section-label')
                    with ui.row().classes('w-full gap-3').style('margin-bottom: 12px;'):
                        pickup = ui.input('Pickup Postal Code').classes('flex-1')
                        drop = ui.input('Drop Postal Code').classes('flex-1')
                    with ui.row().classes('w-full gap-3').style('margin-bottom: 16px;'):
                        pickup_time = ui.input('Pickup Time').props('type="datetime-local"').classes('flex-1')
                        drop_time = ui.input('Drop Time').props('type="datetime-local"').classes('flex-1')

                    ui.separator().style('margin: 16px 0;')

                    ui.label('Execution Mode').classes('section-label')
                    with ui.row().classes('items-center gap-4').style('margin-bottom: 16px; padding: 12px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;'):
                        environment_mode = ui.radio(['DEBUG', 'PRODUCTION'], value='DEBUG').props('inline')

                    ui.separator().style('margin: 16px 0;')

                    ui.label('Bill Images').classes('section-label')
                    upload_ui = ui.upload(
                        label='Drop files here or click to browse',
                        multiple=True,
                        on_upload=handle_single_upload,
                    ).on('added', handle_added).classes('w-full').style('margin-bottom: 20px;')

                    ui.button('Run Fraud Detection →', on_click=lambda: submit_job()) \
                        .classes('w-full main-btn').style('height: 48px;')

                # ── RIGHT: Status + Pipeline Cards ──
                with ui.column().style('flex: 1; min-width: 340px; gap: 16px;'):

                    # Job Status Card
                    with ui.card().style('padding: 24px; border: 1px solid #e2e8f0; width: 100%;'):
                        with ui.row().classes('items-center gap-3').style('margin-bottom: 20px;'):
                            with ui.element('div').style('width: 40px; height: 40px; background: linear-gradient(135deg, #f0fdf4, #dcfce7); border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;'):
                                ui.label('📡').style('font-size: 18px;')
                            with ui.column().style('gap: 2px;'):
                                ui.label('Job Status').style('font-size: 18px; font-weight: 700; color: #0f172a;')
                                ui.label('Real-time processing updates').style('font-size: 12px; color: #94a3b8;')

                        with ui.row().classes('items-center gap-3').style('padding: 14px 16px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 14px;'):
                            spinner = ui.spinner(size='sm')
                            spinner.set_visibility(False)
                            status = ui.label('Status: Idle').style('font-size: 13px; font-weight: 600; color: #475569;')

                        with ui.column().classes('w-full gap-2').style('padding: 14px 16px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label('Progress').style('font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.08em; text-transform: uppercase;')
                                progress_text = ui.label('0% complete').style('font-size: 12px; color: #6366f1; font-family: "DM Mono", monospace; font-weight: 500;')
                            progress_bar = ui.linear_progress(value=0).classes('w-full').style('height: 8px; border-radius: 6px; margin-top: 8px;')

                    # Pipeline Stages Card
                    with ui.card().style('padding: 24px; border: 1px solid #e2e8f0; width: 100%;'):
                        ui.label('Pipeline Stages').style('font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 16px;')

                        stages = [
                            ('📤', 'File Upload', '#eef2ff', '#6366f1'),
                            ('🔍', 'OCR Extraction', '#f0fdf4', '#22c55e'),
                            ('🧠', 'AI Normalization', '#fefce8', '#ca8a04'),
                            ('⚠️', 'Fraud Analysis', '#fef2f2', '#ef4444'),
                        ]
                        for i, (icon, label_text, bg, color) in enumerate(stages):
                            with ui.row().classes('w-full items-center gap-3').style(f'padding: 12px 14px; background: {bg}; border-radius: 10px; margin-bottom: {"8px" if i < len(stages)-1 else "0"};'):
                                ui.label(icon).style('font-size: 16px; width: 24px; text-align: center;')
                                ui.label(label_text).style(f'font-size: 13px; font-weight: 600; color: {color}; flex: 1;')
                                with ui.element('div').style(f'width: 8px; height: 8px; background: {color}; border-radius: 50%; opacity: 0.5;'):
                                    pass

        # ============================================================
        # TAB 2 — ANALYTICS
        # ============================================================
        with ui.tab_panel('Analytics').style('padding: 28px 36px;'):
            with ui.column().classes('w-full').style('max-width: 1200px; margin: 0 auto; gap: 20px;'):

                with ui.row().classes('w-full items-center justify-between').style('margin-bottom: 4px;'):
                    with ui.column().style('gap: 4px;'):
                        ui.label('LLM Analytics').style('font-size: 26px; font-weight: 700; color: #0f172a; letter-spacing: -0.02em;')
                        ui.label('Token usage and cost breakdown across all AI models').style('font-size: 13px; color: #94a3b8;')
                    ui.button('↻  Refresh Data', on_click=refresh_analytics).classes('refresh-btn').style('padding: 10px 20px;')

                # ── Row 1: Groq Normalization + Groq Fraud ──
                with ui.row().classes('w-full gap-5'):

                    # Groq Normalization
                    with ui.card().style('flex: 1; padding: 22px; border: 1px solid #e0e7ff;'):
                        with ui.row().classes('items-center justify-between').style('margin-bottom: 18px;'):
                            with ui.row().classes('items-center gap-3'):
                                with ui.element('div').style('width: 36px; height: 36px; background: linear-gradient(135deg, #eef2ff, #e0e7ff); border-radius: 9px; display: flex; align-items: center; justify-content: center;'):
                                    ui.label('🚀').style('font-size: 16px;')
                                with ui.column().style('gap: 2px;'):
                                    ui.label('Groq Normalization').style('font-size: 13px; font-weight: 700; color: #0f172a;')
                                    ui.label('llama-3.1-8b-instant').style('font-size: 10px; color: #94a3b8; font-family: "DM Mono", monospace;')
                            groq_norm_cost = ui.label('£0.0000').style('font-size: 20px; font-weight: 700; color: #6366f1; font-family: "DM Mono", monospace;')

                        with ui.grid(columns=3).classes('w-full gap-3'):
                            for lbl_text, ref_key in [('API Calls', 'gnc'), ('Input Tokens', 'gnti'), ('Output Tokens', 'gnto')]:
                                with ui.element('div').classes('stat-chip'):
                                    ui.label(lbl_text.upper()).style('font-size: 9px; font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;')
                                    lbl = ui.label('0').style('font-size: 20px; font-weight: 700; color: #0f172a; font-family: "DM Mono", monospace; margin-top: 4px;')
                                    if ref_key == 'gnc': groq_norm_calls = lbl
                                    elif ref_key == 'gnti': groq_norm_tokens_in = lbl
                                    elif ref_key == 'gnto': groq_norm_tokens_out = lbl

                    # Groq Fraud
                    with ui.card().style('flex: 1; padding: 22px; border: 1px solid #fee2e2;'):
                        with ui.row().classes('items-center justify-between').style('margin-bottom: 18px;'):
                            with ui.row().classes('items-center gap-3'):
                                with ui.element('div').style('width: 36px; height: 36px; background: linear-gradient(135deg, #fef2f2, #fee2e2); border-radius: 9px; display: flex; align-items: center; justify-content: center;'):
                                    ui.label('🔍').style('font-size: 16px;')
                                with ui.column().style('gap: 2px;'):
                                    ui.label('Groq Fraud Detection').style('font-size: 13px; font-weight: 700; color: #0f172a;')
                                    ui.label('llama-3.3-70b-versatile').style('font-size: 10px; color: #94a3b8; font-family: "DM Mono", monospace;')
                            groq_fraud_cost = ui.label('£0.0000').style('font-size: 20px; font-weight: 700; color: #ef4444; font-family: "DM Mono", monospace;')

                        with ui.grid(columns=3).classes('w-full gap-3'):
                            for lbl_text, ref_key in [('API Calls', 'gfc'), ('Input Tokens', 'gfti'), ('Output Tokens', 'gfto')]:
                                with ui.element('div').classes('stat-chip'):
                                    ui.label(lbl_text.upper()).style('font-size: 9px; font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;')
                                    lbl = ui.label('0').style('font-size: 20px; font-weight: 700; color: #0f172a; font-family: "DM Mono", monospace; margin-top: 4px;')
                                    if ref_key == 'gfc': groq_fraud_calls = lbl
                                    elif ref_key == 'gfti': groq_fraud_tokens_in = lbl
                                    elif ref_key == 'gfto': groq_fraud_tokens_out = lbl

                # ── Row 2: Google Vision + Combined Total ──
                with ui.row().classes('w-full gap-5'):

                    with ui.card().style('flex: 2; padding: 22px; border: 1px solid #dbeafe;'):
                        with ui.row().classes('items-center justify-between').style('margin-bottom: 18px;'):
                            with ui.row().classes('items-center gap-3'):
                                with ui.element('div').style('width: 36px; height: 36px; background: linear-gradient(135deg, #eff6ff, #dbeafe); border-radius: 9px; display: flex; align-items: center; justify-content: center;'):
                                    ui.label('📸').style('font-size: 16px;')
                                with ui.column().style('gap: 2px;'):
                                    ui.label('Google Vision OCR').style('font-size: 13px; font-weight: 700; color: #0f172a;')
                                    ui.label('cloud vision api').style('font-size: 10px; color: #94a3b8; font-family: "DM Mono", monospace;')
                            gcv_cost = ui.label('£0.0000').style('font-size: 20px; font-weight: 700; color: #3b82f6; font-family: "DM Mono", monospace;')

                        with ui.grid(columns=2).classes('w-full gap-3'):
                            for lbl_text, ref_key in [('API Calls', 'gcc'), ('Images Processed', 'gci')]:
                                with ui.element('div').classes('stat-chip'):
                                    ui.label(lbl_text.upper()).style('font-size: 9px; font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;')
                                    lbl = ui.label('0').style('font-size: 20px; font-weight: 700; color: #0f172a; font-family: "DM Mono", monospace; margin-top: 4px;')
                                    if ref_key == 'gcc': gcv_calls = lbl
                                    elif ref_key == 'gci': gcv_images = lbl

                    with ui.card().style('flex: 1; padding: 22px; background: linear-gradient(135deg, #f5f3ff, #ede9fe) !important; border: 1px solid #ddd6fe; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 140px;'):
                        ui.label('TOTAL SPEND').style('font-size: 10px; font-weight: 700; color: #7c3aed; letter-spacing: 0.12em; margin-bottom: 10px;')
                        combined_total = ui.label('£0.0000').style('font-size: 38px; font-weight: 700; color: #6366f1; font-family: "DM Mono", monospace; letter-spacing: -0.02em;')
                        ui.label('all models combined').style('font-size: 11px; color: #a5b4fc; margin-top: 6px;')

                # ── Per-job table ──
                with ui.card().style('padding: 22px; border: 1px solid #e2e8f0; width: 100%;'):
                    with ui.column().style('gap: 3px; margin-bottom: 16px;'):
                        ui.label('Cost by Job').style('font-size: 16px; font-weight: 700; color: #0f172a;')
                        ui.label('Last 10 submitted jobs').style('font-size: 12px; color: #94a3b8;')

                    jobs_table = ui.table(
                        columns=[
                            {'name': 'job_id', 'label': 'Job ID', 'field': 'job_id', 'align': 'left'},
                            {'name': 'total_cost', 'label': 'Total Cost', 'field': 'total_cost', 'align': 'right'},
                            {'name': 'created_at', 'label': 'Created At', 'field': 'created_at', 'align': 'right'},
                        ],
                        rows=[]
                    ).classes('w-full')


ui.run(title='ExpenseAI — Fraud Detection', port=8080, favicon='⬡')