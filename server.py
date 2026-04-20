<!DOCTYPE html>
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
.files.list{grid-template-columns:1fr;gap:4px}
.files.list .file{display:flex;flex-direction:row;align-items:center;padding:8px 16px;gap:12px}
.files.list .file-icon{margin-bottom:0;width:32px;height:32px}
.files.list .file-name{flex:1}
.files.list .file-size{width:80px;text-align:right}
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
<button id="folderBtn" onclick="loadFiles()">My Drive</button>/button>
</div>
<div class="content">
<div id="folderTitle" style="padding:12px;font-size:20px;">My Drive</div>
<div class="toolbar">
<button onclick="createFolder()" title="New folder"><span class="material-icons">create_new_folder</span></button>
<button onclick="document.getElementById('fileInput').click()"><span class="material-icons">cloud_upload</span></button>
<button onclick="handleDelete()" title="Delete"><span class="material-icons">delete</span></button>
<button onclick="toggleView()" title="Toggle view"><span class="material-icons" id="viewIcon">grid_view</span></button>
<select id="sortSelect" onchange="sortFiles(this.value)" style="background:var(--bg2);color:var(--text);border:1px solid #444;padding:8px;border-radius:8px;height:40px">
<option value="date">Date added</option>
<option value="name">Name</option>
<option value="size">Size</option>
<option value="type">Type</option>
</select>
</div>
<input type="file" id="fileInput" hidden onchange="upload(this)">
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
</div>
<script>
var files = [];
var selected = [];
var currentFolder = null;
var viewMode = localStorage.getItem('viewMode') || 'grid';
var sortBy = localStorage.getItem('sortBy') || 'date';

function toggleView() {
    viewMode = viewMode === 'grid' ? 'list' : 'grid';
    localStorage.setItem('viewMode', viewMode);
    document.getElementById('files').className = 'files ' + viewMode;
    document.getElementById('viewIcon').textContent = viewMode === 'grid' ? 'grid_view' : 'view_list';
}

function sortFiles(field) {
    sortBy = field;
    localStorage.setItem('sortBy', sortBy);
    render();
}

function getExt(f) {
    return (f.filename || '').split('.').pop().toLowerCase();
}

function sortItems(items) {
    return items.slice().sort(function(a, b) {
        if(sortBy === 'name') {
            var na = (a.filename || a.folder || '').toLowerCase();
            var nb = (b.filename || b.folder || '').toLowerCase();
            return na.localeCompare(nb);
        }
        if(sortBy === 'size') {
            return (b.size || 0) - (a.size || 0);
        }
        if(sortBy === 'type') {
            return getExt(a).localeCompare(getExt(b));
        }
        return (b.date || 0) - (a.date || 0);
    });
}

function createFolder() {
    var name = prompt("Folder name:");
    if(!name) return;
    var fullName = currentFolder ? currentFolder + '/' + name : name;
    fetch("/create_folder", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({name: fullName})
    }).then(function(r){return r.json()}).then(function(d){
        loadFiles();
    });
}

function loadFiles() {
    currentFolder = localStorage.getItem('currentFolder') || null;
    fetch("/files").then(function(r){return r.json()}).then(function(data){
        files = data;
        render();
    });
}

function goFolder(name) {
    console.log('goFolder:', name);
    if(name === null) {
        currentFolder = null;
    } else if(!currentFolder) {
        currentFolder = name;
    } else {
        currentFolder = currentFolder + '/' + name;
    }
    localStorage.setItem('currentFolder', currentFolder || '');
    render();
}

function goUp() {
    if(!currentFolder || !currentFolder.includes('/')) {
        currentFolder = null;
    } else {
        currentFolder = currentFolder.substring(0, currentFolder.lastIndexOf('/'));
    }
    localStorage.setItem('currentFolder', currentFolder || '');
    render();
}

function getFolderFiles(folder) {
    if(!folder) return files.filter(function(f){return !f.folder && !f.is_folder;});
    var prefix = folder + '/';
    return files.filter(function(f){
        return !f.is_folder && ((f.folder === folder) || (f.folder && f.folder.startsWith(prefix)));
    });
}

function getFolders() {
    console.log('getFolders, currentFolder:', currentFolder);
    if(!currentFolder) {
        var foldersAtRoot = files.filter(function(f){return f.folder && !f.folder.includes('/') && f.is_folder;}).map(function(f){return f.folder;});
        var r = [...new Set(foldersAtRoot)];
        console.log('root folders:', r);
        return r;
    } else {
        var prefix = currentFolder + '/';
        var subfolders = files.filter(function(f){return f.folder && f.folder.startsWith(prefix) && f.is_folder;}).map(function(f){return f.folder.substring(prefix.length).split('/')[0];});
        var r = [...new Set(subfolders)];
        console.log('subfolders of', currentFolder + ':', r);
        return r;
    }
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
    var allFolders = currentFolder ? getFolders() : getFolders().filter(function(f){return f && f !== currentFolder;});
    var folders = sortItems(allFolders.filter(function(f){return f && f !== currentFolder;}).map(function(f){return {folder: f, is_folder: true};}));
    var folderNames = folders.map(function(f){return f.folder;});
    
    var allFiles = currentFolder ? getFolderFiles(currentFolder) : files.filter(function(f){return !f.folder && !f.is_folder;});
    var sortedFiles = sortItems(allFiles);
    console.log('folders:', folderNames, 'fv:', sortedFiles.length);
    
    var el = document.getElementById("files");
    el.className = 'files ' + viewMode;
    if(document.getElementById('viewIcon')) {
        document.getElementById('viewIcon').textContent = viewMode === 'grid' ? 'grid_view' : 'view_list';
    }
    if(document.getElementById('sortSelect')) {
        document.getElementById('sortSelect').value = sortBy;
    }
    if(!currentFolder && !sortedFiles.length && !folderNames.length) { el.innerHTML = '<div class="empty">Empty</div>'; return; }
    if(currentFolder && !sortedFiles.length && !folderNames.length) { sortedFiles = []; }
    var html = "";
    
    if(currentFolder) {
        html += '<div class="file" onclick="goUp()"><div class="file-icon"><span class="material-icons">arrow_upward</span></div><div class="file-name">..</div></div>';
    }
    
    for(var i=0; i<folderNames.length; i++) {
        html += '<div class="file folder" data-folder="' + folderNames[i] + '" onclick="goFolder(this.dataset.folder)"><div class="file-icon"><span class="material-icons">folder</span></div><div class="file-name">' + folderNames[i] + '</div></div>';
    }
    
    for(var i=0; i<sortedFiles.length; i++) {
        var f = sortedFiles[i];
        var fname = f.filename || "Untitled";
        var fsize = fmt(f.size);
        var icon = getIcon(f);
        var sel = selected.indexOf(f.id) >= 0 ? ' selected' : '';
        html += '<div class="file' + sel + '" onclick="toggle(' + f.id + ')"><div class="file-icon"><span class="material-icons">' + icon + '</span></div><div class="file-name">' + fname + '</div><div class="file-size">' + fsize + '</div></div>';
    }
    el.innerHTML = html;
    var btn = document.getElementById("folderBtn"); var title = document.getElementById("folderTitle"); if(btn) btn.textContent = currentFolder || "My Drive"; if(title) title.textContent = currentFolder || "My Drive";
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

function deleteFolder() {
    if(!currentFolder) { alert("Select a folder first"); return; }
    if(!confirm("Delete all files in folder \"" + currentFolder + "\"")) return;
    var parentFolder = currentFolder.includes('/') ? currentFolder.substring(0, currentFolder.lastIndexOf('/')) : null;
    fetch("/delete_folder", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({folder: currentFolder})
    }).then(function(r){return r.json()}).then(function(d){
        alert("Deleted " + d.deleted + " files!");
        currentFolder = parentFolder;
        localStorage.setItem('currentFolder', currentFolder || '');
        loadFiles();
    }).catch(function(e){alert("Error: " + e.message)});
}

function handleDelete() {
    if(selected.length > 0) {
        deleteFiles();
    } else if(currentFolder) {
        deleteFolder();
    } else {
        showT("Select files or open a folder to delete");
    }
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
</html>