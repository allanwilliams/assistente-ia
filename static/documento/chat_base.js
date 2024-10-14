const maxFileSizePdf = 32
const maxFileSizeMedia = 200
const csrf_token = $('#csrf_token').val()

const documentType = [
    'application/pdf'
]
const audioTypes = [
    'audio/midi',
    'audio/mpeg',
    'audio/webm',
    'audio/ogg',
    'audio/wav',    
]
const videoTypes = [
    'video/webm',
    'video/ogg',
    'video/mp4',
    'video/x-msvideo',
    'video/x-ms-asf',
    'application/vnd.ms-asf',
    '.asf'
]
const mediaTranscriptionTypes = audioTypes.concat(videoTypes)


$(document).ready(() =>{
    $.ajaxSetup({
        headers: {"X-CSRFToken": csrf_token },
    });

    $('select:not(.filtered):not(.admin-autocomplete)').select2({dropdownAutoWidth : true});
})

function getUserChats(userId, api) {
    return fetch(`/documento/api/${api}/?criado_por=${userId}&ativo=true`)
}
function showMessage(text,duration){
    Toastify({
        text,
        duration,
        close: true,
        gravity: "top", // `top` or `bottom`
        position: "center", // `left`, `center` or `right`
        stopOnFocus: true, // Prevents dismissing of toast on hover
        style: {
            background: "linear-gradient(to right, #00b09b, #96c93d)",
        },
        onClick: function(){} // Callback after click
    }).showToast();
}

const convertHexToRGBA = (hexCode, opacity = 1) => {  
    let hex = hexCode.replace('#', '');
    
    if (hex.length === 3) {
        hex = `${hex[0]}${hex[0]}${hex[1]}${hex[1]}${hex[2]}${hex[2]}`;
    }    
    
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    if (opacity > 1 && opacity <= 100) {
        opacity = opacity / 100;   
    }

    return `rgba(${r},${g},${b},${opacity})`;
};

function validateDocument(allowedTypes, target){
    const file = target.files[0]
    return allowedTypes.indexOf(file.type) != -1
}

function isValidSizes(maxFileSize, file) {
    const fileName = file.name;
    const fileSize = file.size;

    let sizeInMB = Number.parseFloat(fileSize * 0.000001).toFixed(2);

    if (sizeInMB >= maxFileSize) {
        Swal.fire({
            icon: "error",
            title:`O arquivo excede o tamanho máximo de <b>${maxFileSize} mb</b>.`,
        }).then(() => window.location.reload());
        return false
    }

    if (fileName.length > 99) {
        Swal.fire({
            icon: "error",
            title:`O nome do arquivo deve ter menos de 100 caracteres.`,
        }).then(() => window.location.reload());
        return false
    }

    return true
}

function setUrlParams(param, value) {
    const urlParams = new URLSearchParams(location.search);
    urlParams.set(param, value);
    window.history.replaceState({}, '', `${location.pathname}?${urlParams}`);
}