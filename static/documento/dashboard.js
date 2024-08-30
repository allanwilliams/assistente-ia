
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
const documentoLink = $('#documento-link')
const documentoDelete = $('#documento-delete')

$(document).ready(() => {

    $('[data-toggle="tooltip"]').tooltip()

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
            else newChat(target)
        }else{
            Swal.fire({
                icon: "error",
                title: "Tipo de arquivo não suportado",
                confirmButtonColor:'#00c0ef'
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
            else newChat(target)
        }else{
            Swal.fire({
                icon: "error",
                title: "Tipo de arquivo não suportado",
                confirmButtonColor:'#00c0ef'
            }).then(() => {
                window.location.reload()
            });
        }
    });        
    getDocumentsChats()
    setInterval(() => getDocumentsChats(), 7000)
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
                    fillListChats(ultimo)
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

// function dialogVerifyScannedPdf(target) {
//     const file = target.files[0]
//     Swal.fire({
//         title: "Seu PDF é escaneado ou possui imagens em seu conteúdo?",
//         text: "Essa informação é importante para sabermos se precisamos fazer um processamento avançado do seu PDF para obter dados contidos na imagens.",
//         // imageUrl: "https://images.wondershare.com/pdfelement/faq/scanned.png",
//         // imageWidth: 400,
//         // imageHeight: 200,
//         // imageAlt: "Custom image",
//         showCancelButton: true,
//         showDenyButton: true,
//         // confirmButtonColor: "#3085d6",
//         // cancelButtonColor: "#3085d6",
//         confirmButtonText: "Sim, processar meu PDF",
//         denyButtonText: "Não processar meu PDF",
//         cancelButtonText: "Cancelar",
//         width: '50em'
//     }).then((result) => {
//         const scanned = result.isConfirmed
//         // newChat(file, scanned)
//     });
// }

function newChat(target) {
    const file = target.files[0]
    const formData = new FormData()
    formData.append('titulo', file.name)
    formData.append('documento', file)
    formData.append('ativo', true)
    
    const STATUS_OCR_FILA = 1
    formData.append('status', STATUS_OCR_FILA)

    if(isValidSizes(maxFileSizePdf, file)) {
        $.ajax({
            type:'POST',
            url: `/documento/api/chat/`,
            beforeSend: () => loader.fadeIn(),
            data: formData,
            contentType: false,
            processData: false,
            success: (data) => {
                Swal.fire({
                    icon: "success",
                    title: 'Recebemos seu PDF!',
                    text: 'Iniciaremos em breve o processamento do seu PDF para extrair o máximo de informações e usá-las na nossa inteligência artificial. Você pode acompanhar o andamento desse processo aqui mesmo na Dashboard!',
                    confirmButtonColor:'#00c0ef'
                }).then(() => {
                    window.location.reload()
                });
            },
            error: (error) => {
                const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."

                Swal.fire({
                    icon: "error",
                    title: mensagem,
                    confirmButtonColor:'#00c0ef'
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
                Swal.fire({
                    icon: "success",
                    title: 'Recebemos seu arquivo!',
                    text: 'Iniciaremos em breve o processamento do seu arquivo para extrair o máximo de informações e usá-las na nossa inteligência artificial. Você pode acompanhar o andamento desse processo aqui mesmo na Dashboard!',
                    confirmButtonColor:'#00c0ef'
                }).then(() => {
                    window.location.reload()
                });
            },
            error: (error) => {
                const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."

                Swal.fire({
                    icon: "error",
                    title: mensagem,
                    confirmButtonColor:'#00c0ef'
                }).then(() => {
                    window.location.reload()
                });
            },
            complete: () => loader.fadeOut()
        })
    }
}

function fillListChats(chat) {

    const firstStep = $(".main-progress-bar .first");
    const secondStep = $(".main-progress-bar .second");
    const thirdStep = $(".main-progress-bar .third");
    const fourthStep = $(".main-progress-bar .fourth");
    const progressbarStatusText = $("#progress-bar-status-text");
    const progressMediaTitulo = $("#progress-media-titulo");

    const getProgress = (status) => {
        
        const progress = {
            1: { step: 1, classColor: '', color: '#00c0ef'},
            2: { step: 2, classColor: '', color: '#00c0ef'},
            3: { step: 3, classColor: '', color: '#00c0ef'},
            4: { step: 4, classColor: 'bg-success', color: '#5cb85c'},
            5: { step: 5, classColor: 'bg-danger', color: '#ff0000'},
            6: { step: 5, classColor: 'bg-danger', color: '#ff0000', stepEl: secondStep, beforeStep: firstStep},
            7: { step: 5, classColor: 'bg-danger', color: '#ff0000', stepEl: thirdStep, beforeStep: secondStep},
        }

        return progress[status] || progress[1]
    }

    if(chat) {
        const progress = getProgress(chat.status)

        ([1, 6, 7].includes(chat.status)) ? documentoDelete.css('display','block') : documentoDelete.css('display','none');

        if (progress.step > 0 && progress.step < 5) {
            firstStep.addClass('active').addClass('running')
        }
        
        if (progress.step > 1) {
            secondStep.addClass('active').addClass('running')
            firstStep.removeClass('running')
        }
        
        if (progress.step > 2){
            thirdStep.addClass('active').addClass('running')
            secondStep.removeClass('running')
        }
        
        if (progress.step == 4) {
            fourthStep.addClass('active')
            thirdStep.removeClass('running')
            documentoLink.css('display','block')
            documentoLink.attr('href',`/documento/${redirect}=${chat.id}`)
        }
        documentoDelete.attr('data-remove-id',`${chat.id}`)

        if (progress.step > 4){
            if (progress.stepEl == secondStep) thirdStep.removeClass('running').removeClass('active')
            if(progress.stepEl) progress.stepEl.removeClass('running').addClass('active').addClass('error')
            if(progress.beforeStep) progress.beforeStep.removeClass('running')
        }
        
        progressbarStatusText.text(chat.status_str)
        progressbarStatusText.css('color', progress.color) 
        progressMediaTitulo.text(chat.titulo)


    }
    $(".conteudo-documentos").fadeIn()
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