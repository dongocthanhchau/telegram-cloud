import os, asyncio, aiofiles
from pathlib import Path
from telethon import TelegramClient, types
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
import json

DATA_DIR = Path("/home/chad/telegram-cloud/data")
DATA_DIR.mkdir(exist_ok=True)

API_ID = 32699255
API_HASH = "0c30b4b3e7882eb48287f76228411411"
CHANNEL_ID = -1003992405929
SESSION_FILE = "/home/chad/.local/share/telegram-cloud/session.session"

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TGStorage</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#1f1f1f;--bg2:#2d2d2d;--hover:#3d3d3d;--text:#e8eaed;--text2:#9aa0a6;--blue:#8ab4f8}
body{font-family:Roboto,sans-serif;background:var(--bg);color:var(--text);height:100vh}
.main{display:flex}
.sidebar{width:220px;padding:16px}
.sidebar button{width:100%;padding:12px;text-align:left;background:var(--bg2);border:none;color:var(--text);cursor:pointer;margin:4px 0;border-radius:8px}
.sidebar button:hover{background:var(--hover)}
.content{flex:1;padding:24px;overflow-y:auto}
.toolbar{display:flex;gap:12px;padding:16px 0}
.toolbar button{width:40px;height:40px;border-radius:50%;background:none;border:none;color:var(--text2);cursor:pointer}
.toolbar button:hover{background:var(--hover);color:var(--text)}
.files{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}
.file{padding:16px;border-radius:8px;cursor:pointer;background:var(--bg2)}
.file:hover{background:var(--hover)}
.file.selected{border:2px solid var(--blue)}
.file-icon{width:40px;height:40px;border-radius:8px;background:linear-gradient(135deg,#94a3b8,#64748b);display:flex;align-items:center;justify-content:center;margin-bottom:8px}
.file-name{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.file-size{font-size:12px;color:var(--text2)}
.fab{position:fixed;bottom:24px;right:24px;width:56px;height:56px;background:linear-gradient(135deg,#39c5cf,#2196f3);border-radius:16px;display:flex;align-items:center;justify-content:center;cursor:pointer}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--hover);padding:12px 24px;border-radius:8px;display:none}
.toast.show{display:block}
.modal{position:fixed;inset:0;background:rgba(0,0,0,0.8);display:none;align-items:center;justify-content:center;z-index:100}
.modal.show{display:flex}
.modal-content{background:var(--bg2);padding:24px;border-radius:8px;min-width:300px}
.modal-content input{width:100%;padding:12px;background:var(--bg);border:1px solid #444;border-radius:4px;color:var(--text)}
.modal-content .btns{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
.modal-content button{padding:10px 20px;border-radius:4px;border:none;cursor:pointer}
.modal-content .cancel{background:transparent;color:var(--text2)}
.modal-content .confirm{background:var(--blue);color:#1f1f1f}
.actions{position:fixed;bottom:80px;left:50%;transform:translateX(-50%);background:var(--bg2);padding:8px 16px;border-radius:24px;display:none;gap:8px}
.actions.show{display:flex}
.actions button{padding:10px 16px;border-radius:16px;background:var(--hover);border:none;color:var(--text);cursor:pointer}
.empty{text-align:center;padding:60px;color:var(--text2)}
</style>
</head>
<body>
<div class="main">
<div class="sidebar">
<div style="padding:12px;font-size:18px;font-weight:500">Storage</div>
<button onclick="loadFiles()">My Drive</button>
</div>
<div class="content">
<div class="toolbar">
<button onclick="document.getElementById('fileInput').click()"><span class="material-icons">cloud_upload</span></button>
</div>
<div class="files" id="files"></div>
</div>
</div>
<input type="file" id="fileInput" multiple style="display:none" onchange="upload(this.files)">
<div class="fab" onclick="document.getElementById('fileInput').click()"><span class="material-icons">add</span></div>
<div class="toast" id="toast"></div>
<div class="modal" id="modal">
<div class="modal-content">
<h3>Rename</h3>
<input id="newName">
<div class="btns"><button class="cancel" onclick="closeModal()">Cancel</button><button class="confirm" onclick="saveRename()">Save</button></div>
</div>
</div>
<div class="actions" id="actions">
<button onclick="downloadFile()">Download</button>
<button onclick="showRename()">Rename</button>
<button onclick="deleteFiles()">Delete</button>
</div>
<script>
var files = [];
var selected = [];

function loadFiles() {
    fetch("/files").then(function(r){return r.json()}).then(function(data){
        files = data;
        render();
    });
}

function fmt(b) {
    if(!b) return "";
    if(b < 1024) return b + " B";
    if(b < 1048576) return (b/1024).toFixed(1) + " KB";
    if(b < 1073741824) return (b/1048576).toFixed(1) + " MB";
    return (b/1073741824).toFixed(1) + " GB";
}

function getIcon(f) {
    var ext = (f.filename||"").split(".").pop().toLowerCase();
    if(["jpg","png","gif","webp"].indexOf(ext) >= 0) return "image";
    if(["mp4","mov"].indexOf(ext) >= 0) return "videocam";
    if(ext === "pdf") return "picture_as_pdf";
    if(["txt","doc"].indexOf(ext) >= 0) return "description";
    return "insert_drive_file";
}

function toggle(id) {
    if(selected.indexOf(id) >= 0) {
        selected = [];
    } else {
        selected = [id];
    }
    document.getElementById("actions").classList.toggle("show", selected.length > 0);
    render();
}

function render() {
    var el = document.getElementById("files");
    if(!files.length) { el.innerHTML = '<div class="empty">No files</div>'; return; }
    var html = "";
    for(var i=0; i<files.length; i++) {
        var f = files[i];
        var fname = f.filename || "Untitled";
        var fsize = fmt(f.size);
        var icon = getIcon(f);
        var sel = selected.indexOf(f.id) >= 0 ? ' selected' : '';
        html += '<div class="file' + sel + '" onclick="toggle(' + f.id + ')">' +
            '<div class="file-icon"><span class="material-icons">' + icon + '</span></div>' +
            '<div class="file-name">' + fname + '</div>' +
            '<div class="file-size">' + fsize + '</div></div>';
    }
    el.innerHTML = html;
}

function downloadFile() {
    if(selected.length !== 1) { showT("Select 1 file"); return; }
    window.location.href = "/download/" + selected[0];
}

function showRename() {
    if(selected.length !== 1) { showT("Select 1 file"); return; }
    var f = files.find(function(x){return x.id === selected[0]});
    document.getElementById("newName").value = f.filename || "";
    document.getElementById("modal").classList.add("show");
}

function closeModal() { document.getElementById("modal").classList.remove("show"); }

function saveRename() {
    var name = document.getElementById("newName").value;
    if(!name || selected.length !== 1) return;
    fetch("/rename", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({file_id: selected[0], new_name: name})
    }).then(function(r){return r.json()}).then(function(d){
        closeModal();
        showT("Done!");
        selected = [];
        document.getElementById("actions").classList.remove("show");
        loadFiles();
    }).catch(function(e){showT("Error: " + e.message)});
}

function deleteFiles() {
    if(!selected.length) return;
    if(!confirm("Delete " + selected.length + " file(s)?")) return;
    fetch("/delete", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({file_ids: selected})
    }).then(function(r){return r.json()}).then(function(d){
        showT("Deleted!");
        selected = [];
        document.getElementById("actions").classList.remove("show");
        loadFiles();
    }).catch(function(e){showT("Error: " + e.message)});
}

function upload(fs) {
    if(!fs.length) return;
    showT("Uploading...");
    var promises = [];
    for(var i=0; i<fs.length; i++) {
        (function(f){
            var fd = new FormData();
            fd.append("file", f);
            promises.push(fetch("/upload", {method: "POST", body: fd}));
        })(fs[i]);
    }
    Promise.all(promises).then(function(){
        showT("Done!");
        loadFiles();
    }).catch(function(e){showT("Error: " + e.message)});
}

function showT(m) {
    var t = document.getElementById("toast");
    t.textContent = m;
    t.classList.add("show");
    setTimeout(function(){t.classList.remove("show")}, 3000);
}

loadFiles();
</script>
</body>
</html>"""

app = FastAPI()


@app.on_event("startup")
async def s():
    await client.start()


@app.on_event("shutdown")
async def d():
    await client.disconnect()


@app.get("/")
def root():
    return HTMLResponse(HTML)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    p = DATA_DIR / file.filename
    async with aiofiles.open(p, "wb") as f:
        await f.write(await file.read())
    await client.send_file(CHANNEL_ID, p, caption=file.filename)
    os.remove(p)
    return {"ok": 1}


@app.get("/files")
async def files():
    msgs = await client.get_messages(CHANNEL_ID, limit=100)
    r = []
    for m in msgs:
        if m.file:
            can_rename = (hasattr(m, "document") and m.document is not None) or (
                hasattr(m, "photo") and m.photo is not None
            )
            ts = int(m.date.timestamp()) if m.date else 0
            fn = m.text or (m.file.name if hasattr(m.file, "name") else f"file_{m.id}")
            r.append(
                {
                    "id": m.id,
                    "filename": fn,
                    "size": m.file.size,
                    "date": ts,
                    "renameable": can_rename,
                }
            )
    return r


@app.post("/rename")
async def rename(data: dict):
    fid = data["file_id"]
    new_name = data["new_name"]
    msgs = await client.get_messages(CHANNEL_ID, ids=fid)
    old = msgs
    if hasattr(old, "document") and old.document is not None:
        new_msg = await client.send_file(CHANNEL_ID, old.document, caption=new_name)
        await old.delete()
        return {"ok": 1}
    if hasattr(old, "photo") and old.photo is not None:
        tmp_path = DATA_DIR / f"temp_{fid}_{new_name}"
        await old.download_media(tmp_path)
        await client.send_file(CHANNEL_ID, tmp_path, caption=new_name)
        os.remove(tmp_path)
        await old.delete()
        return {"ok": 1}
    return {"error": "Cannot rename this file"}


@app.post("/delete")
async def delete(data: dict):
    for fid in data["file_ids"]:
        msgs = await client.get_messages(CHANNEL_ID, ids=fid)
        await msgs.delete()
    return {"ok": 1}


@app.get("/download/{fid}")
async def download(fid: int):
    try:
        m = await client.get_messages(CHANNEL_ID, ids=fid)
        if not m or not hasattr(m, "file") or not m.file:
            raise HTTPException(404, "File not found")
        fname = (
            m.text
            or (m.file.name if hasattr(m.file, "name") and m.file.name else None)
            or f"file_{fid}"
        )
        if not fname or fname == f"file_{fid}":
            fname = "download"
        p = DATA_DIR / fname
        await m.download_media(p)
        return FileResponse(p, filename=fname)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
