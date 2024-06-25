
const dropArea = document.querySelector(".drag-area")
const fileInput = dropArea.querySelector(".file-input")
const userId = $("#user-id")
const gridChats = $("#grid-documentos-chats")
const gridQuestion = $("#grid-pergunta-chats")
const body = document.querySelector('body')
const tableDocumentosMedias = $("#table-documentos-medias")
const loader = $("#preloader")
const dominio = $('#dominio').val()
const redirect = $('#redirect').val()

$(document).ready(() => {

    $.ajaxSetup({
        headers: {"X-CSRFToken": csrf_token },
    });

    if(dominio === 'chat') {
        fileInput.accept = documentType.join(',')
    } else {
        fileInput.accept = mediaTranscriptionTypes.join(',')
    }

    body.addEventListener('click', function(event) {
        if(event.target.classList.contains('btn-remove-chat')) {
            const chatId = event.target.attributes['data-remove-id'].value
            deleteChat(chatId)
        }

        // if(event.target.classList.contains('btn-remove-question')) {
        //     const chatId = event.target.attributes['data-id'].value
        //     deleteQuestion(chatId)
        //     event.target.parentElement.parentElement.remove()
        // }        
    })


    fileInput.addEventListener("change", function (e) {
        const target = e.target;
        if(validateDocument(target)){
            const isTranscription = getIsTranscription(target)
            if(isTranscription) newTranscription(target)
            else dialogVerifyScannedPdf(target)
        }else{
            Swal.fire({
                icon: "error",
                title: "Tipo de arquivo não suportado",
            }).then(() => {
                window.location.reload()
            });
        }
    });
    dropArea.onclick = () => {
        fileInput.click();
    };

    dropArea.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropArea.classList.add("drag-active");
    });

    dropArea.addEventListener("dragleave", () => {
        dropArea.classList.remove("drag-active");
    });

    dropArea.addEventListener("drop", (e) => {
        e.preventDefault();
        dropArea.classList.remove("drag-active")
        const target = e.dataTransfer;
        if(validateDocument(target)){
            const isTranscription = getIsTranscription(target)
            if(isTranscription) newTranscription(target)
            else dialogVerifyScannedPdf(target)
        }else{
            Swal.fire({
                icon: "error",
                title: "Tipo de arquivo não suportado",
            }).then(() => {
                window.location.reload()
            });
        }
    });        
    getDocumentsChats()
    setInterval(() => getDocumentsChats(), 13000)
})  

function getDocumentsChats() {

    if(userId.val()) {
        getUserChats(userId.val(), dominio)
        .then((data) => data.json())
        .then((data) => {
            const { results } = data;
            if(results.length) {
                let ultimo = null

                if(dominio === "media-transcricao") {
                    console.log('results', results)
                    const STATUS_CONCLUIDO = 4
                    ultimo = results.filter(i => i.visualizado === false)[0]
                    const concluido = results.filter(i => i.status === STATUS_CONCLUIDO)
                    if(concluido.length) $('.link-acesso').fadeIn()  
                } 

                if(dominio === 'chat') {
                    const STATUS_OCR_DISPENSADO = 8
                    const STATUS_OCR_CONCLUIDO = 4
                    
                    ultimo = results.filter(i => i.visualizado === false && i.status !== STATUS_OCR_DISPENSADO)[0]
                    const concluido = results.filter(i => [STATUS_OCR_DISPENSADO, STATUS_OCR_CONCLUIDO].includes(i.status))
                    if(concluido.length) $('.link-acesso').fadeIn()  
                }

                if (ultimo) {
                    fillListChats([ultimo])
                } else {
                    $(".conteudo-documentos").fadeOut()
                }
            } else {
                $(".conteudo-documentos").fadeOut()
            }
        })
    }
}

function validateDocument(target){
    const file = target.files[0]
    if(dominio === 'chat') {
        return documentType.indexOf(file.type) != -1
    } 
    return mediaTranscriptionTypes.indexOf(file.type) != -1
}

function getIsTranscription(target){
    const file = target.files[0]
    return mediaTranscriptionTypes.indexOf(file.type) != -1
}

function dialogVerifyScannedPdf(target) {
    const file = target.files[0]
    Swal.fire({
        title: "Seu PDF é escaneado?",
        text: "Essa informação é importante para sabermos como processar o seu documento. .",
        imageUrl: "https://images.wondershare.com/pdfelement/faq/scanned.png",
        imageWidth: 400,
        imageHeight: 200,
        imageAlt: "Custom image",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Sim, meu PDF é Escaneado!",
        cancelButtonText: "Não, meu PDF não é Escaneado!",
        width: '50em'
    }).then((result) => {
        const scanned = result.isConfirmed
        newChat(file, scanned)
    });
}

function newChat(file, scannedPdf) {
    const formData = new FormData()
    formData.append('titulo', file.name)
    formData.append('documento', file)
    formData.append('ativo', true)
    
    if(scannedPdf) {
        const STATUS_OCR_FILA = 1
        formData.append('status', STATUS_OCR_FILA)
    }

    if(isValidSizes(maxFileSizePdf, file)) {
        $.ajax({
            type:'POST',
            url: `/documento/api/chat/`,
            beforeSend: () => loader.fadeIn(),
            data: formData,
            contentType: false,
            processData: false,
            success: (data) => {
                if(scannedPdf) {
                    window.location.reload()
                } else {
                    window.location.href = `/documento/chat/?documento=${data.id}`
                }
            },
            error: (error) => {
                const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."

                Swal.fire({
                    icon: "error",
                    title: mensagem,
                }).then(() => {
                    window.location.reload()
                });
            },
            complete: () => loader.fadeOut()
        })
    }

}

function newTranscription(target) {
    const file = target.files[0]
    const tipo = audioTypes.indexOf(file.type) != -1 ? 2 : 1
    const formData = new FormData()
    formData.append('titulo', file.name)
    formData.append('arquivo', file)
    formData.append('ativo', true)
    formData.append('tipo', tipo)

    if(isValidSizes(maxFileSizeMedia, file)) {
        $.ajax({
            type:'POST',
            url: `/documento/api/media-transcricao/`,
            beforeSend: () => loader.fadeIn(),
            data: formData,
            contentType: false,
            processData: false,
            success: (data) => {
                window.location.reload()
            },
            error: (error) => {
                const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."

                Swal.fire({
                    icon: "error",
                    title: mensagem,
                }).then(() => {
                    window.location.reload()
                });
            },
            complete: () => loader.fadeOut()
        })
    }
}

function fillListChats(chats) {
    let list = ''

    // const getIcon = (status) => {
    //     const icons = {
    //         1: { icon: '<i class="fa-solid fa-hourglass-half fa-fade" style="color:orange"></i>', color: 'orange'},
    //         2: { icon:'<i class="fa-solid fa-circle-notch fa-spin" style="color:orange"></i>', color: 'orange'},
    //         3: { icon:'<i class="fa-solid fa-circle-notch fa-spin" style="color:orange"></i>', color: 'orange'},
    //         4: { icon:'<i class="fa-regular fa-circle-check" style="color: #5cb85c"></i>', color: '#5cb85c'},
    //         5: { icon:'<i class="fa-solid fa-ban"></i>', color: 'orange'},
    //         6: { icon:'<i class="fa-solid fa-triangle-exclamation" style="color: #ff0000;"></i>', color: '#ff0000'},
    //         7: { icon:'<i class="fa-solid fa-triangle-exclamation" style="color: #ff0000;"></i>', color: '#ff0000'},
    //     }

    //     return icons[status] || icons[1]
    // }

    const getProgress = (status) => {
        const progress = {
            1: { percent: 15, classColor: 'progress-bar-striped progress-bar-animated bg-info', color: '#00c0ef'},
            2: { percent: 50, classColor: 'progress-bar-striped progress-bar-animated bg-info', color: '#00c0ef'},
            3: { percent: 75, classColor: 'progress-bar-striped progress-bar-animated bg-info', color: '#00c0ef'},
            4: { percent: 100, classColor: 'bg-success', color: '#5cb85c'},
            5: { percent: 100, classColor: 'bg-danger', color: '#ff0000'},
            6: { percent: 100, classColor: 'bg-danger', color: '#ff0000' },
            7: { percent: 100, classColor: 'bg-danger', color: '#ff0000' },
        }

        return progress[status] || progress[1]
    }

    chats.forEach((c) => {
        const progress = getProgress(c.status)
        list += `
            <tr>
                <td>${c.titulo}</td>
                <td> 
                    <div class="progress">
                        <div class="progress-bar ${progress.classColor}" role="progressbar" style="width: ${progress.percent}%;" aria-valuenow="${progress.percent}" aria-valuemin="0" aria-valuemax="100">${progress.percent}%</div>
                    </div>
                    <small style="color:${progress.color}">${c.status_str}</small>
                </td>
                <td class="td-actions">
                    ${c.status === 4 ? 
                        `<a href="/documento/${redirect}=${c.id}">
                            <i style="color:#00c0ef" class='fa fa-eye'></i>
                        </a>` : ''}
                    
                    ${[1, 6, 7].includes(c.status)  ? 
                        `<i data-remove-id='${c.id}' style="color:red" class='fa fa-trash btn-remove-chat'></i>    
                        ` : ``}
                </td>
            </tr>
        `
    })
    $(".conteudo-documentos").fadeIn()

    tableDocumentosMedias.html(list)
}

function deleteChat(chatId) {
    if(chatId) {
        $.ajax({
            type: 'PATCH',
            url: `/documento/api/${dominio}/${chatId}/`,
            data: {
                ativo: false
            },
            complete: () => {
                getDocumentsChats()
            },
        })
    } 
}

// function deleteQuestion(chatId) {
//     if(chatId) {
//         $.ajax({
//             type: 'PATCH',
//             url: `/documento/api/mensagem/${chatId}/`,
//             data: {
//                 is_favorito: false
//             },
//             success: (data) => {
                
//             },
//             error: () => {}
//         })
//     } 
// }    

// function getQuestion(id){
//     fetch(`/documento/api/mensagem/?criado_por=${id}&is_favorito=true`)
//     .then(res=>res.json())
//     .then(data=>{
//         const questions = data.results.reduce((acc,d) => {
//             acc += `<div class='question-div'>
//                         <i style='font-weight: 900;' class="fa-regular fa-circle-question"></i>
//                         <div>
//                             ${d.texto}
//                             <i style='color:#00c0ef;' data-id='${d.id}' class="fa fa-trash btn-remove-question"></i>
//                         </div>
//                     </div>`
//             return acc
            
//         },'')
//         if(questions.length == 0){
//            $('#perguntas_favoritas').hide()
//         }
//         gridQuestion.html(questions)
//     })
// }     
// getQuestion(userId.val())      