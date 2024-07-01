const inputTxtAsk = $('#chat-input-ask')
const btnSendAsk = $("#btn-send-ask")
const listMessagesEl = $("#list-messages")
const chatFormInput = $("#chat-form-input")
const chatIdOpenEl = $('#chat-id-open')
const listChatsEl = $('#list-chats')
const pdfContainer = $('#pdf-obj-container')
const body = document.querySelector('body')
const dropArea = document.querySelector(".drag-area")
const fileInput = dropArea.querySelector(".file-input")
const userId = $("#user-id")
const listaQuestion = $('#lista-question')
const inputask = document.querySelector('#chat-input-ask')
const questionBox = document.querySelector('#questionBox')
const loader = $("#preloader")
const chatHeaderActions = $("#chat-header-actions")
let chatAtual = null

body.addEventListener('click', function(event) {
    if(event.target.classList.contains('btn-page') && chatAtual) {
        const page = event.target.attributes['data-page'].value
        const url = `${chatAtual.documento}#page=${page}`
        loadDocumento(chatAtual.titulo, url)
    }

    if(event.target.classList.contains('choice-link-chat')) {
        const chatId = event.target.attributes['data-id'].value
        getChat(chatId)
    }

    if(event.target.classList.contains('salvar-favoritos')) {
        const msgID = event.target.attributes['data-id'].value
        const favorito = event.target.attributes['data-favorito'].value
        event.target.attributes['data-favorito'].value = !(favorito === 'true')
        
        saveQuestion(msgID, favorito)
        
        event.target.classList.remove('fa-solid')
        event.target.classList.remove('fa-regular')
        
        const CF = (val) => {
            event.target.classList.add(val)
        } 

        (favorito === 'true') ? CF('fa-regular') : CF('fa-solid');
    }

    if(event.target.classList.contains('question')) {
        inputTxtAsk.val(event.target.innerText)
        listaQuestion.html('')
        questionBox.classList.add('hide')            
    } 

    if(event.target.classList.contains('btn-send-fake')) {
        const msgID = event.target.attributes['data-id'].value
        const text = $(`#${msgID}`).text()
        showLatestMessage()
        sendAsk(text)
    }
})

$(document).ready(() => {

    fileInput.accept = documentType.join(',')

    chatFormInput.submit((e) => {
        e.preventDefault()
        const ask = inputTxtAsk.val()
        inputTxtAsk.val('')
        sendAsk(ask)
    })
    
    dropArea.onclick = () => {
        fileInput.click();
    };
    let delaySearchQestion
    inputask.addEventListener('input',(e)=>{
        clearTimeout(delaySearchQestion)
        delaySearchQestion = setTimeout(()=>{getQuestion(userId.val(),e.target.value)},500)
    })
    
    fileInput.addEventListener("change", function (e) {
        const target = e.target;
        newChat(target)
    });

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
        newChat(target)
    });
    
    if(userId.val()) {
        getUserChats(userId.val(), 'chat')
        .then((data) => data.json())
        .then((data) => fillListChats(data.results))
        .then(() => {
            const url = window.location.search
            const urlParams = new URLSearchParams(url);
            const documento = urlParams.get('documento')
            getChat(documento)
        })
    }
})


function fillListChats(chats) {
    let list = ''
    const STATUS_OCR_CONCLUIDO = 4
    const STATUS_OCR_DISPENSADO = 8
    chats = chats.filter(c => [STATUS_OCR_CONCLUIDO, STATUS_OCR_DISPENSADO].includes(c.status))
    chats.forEach((c) => {
       list += `<div class="choice-link-chat btn" data-id="${c.id}">${c.titulo}</div>`
    })

    listChatsEl.html(list)
}


function fillChat(data) {
    const {id, mensagens, titulo, documento, visualizado } = data
    loadDocumento(titulo, documento, id)
    insertConversation(mensagens)
    chatAtual = data
    chatIdOpenEl.val(id)
    prepareActionsChat() 

    let links = $('.choice-link-chat')
    links.removeClass('btn-info')

    let link = links.filter((i, e) => e.attributes['data-id'].value === id.toString())

    if(link.length > 0) {
        link[0].classList.add('btn-info')
    }

    if(!visualizado) {
        updateVisualizado(id)
    }
}

function loadDocumento(titulo, url, id) {
    pdfContainer.html(`
        <div class="pdf-header">
            <h3>${titulo}</h3> 
        </div>
        <embed src='${url}' width="100%" height="100%">
    `)
}


function insertConversation(mensagens) {
    listMessagesEl.empty()

    const fakeConversation = `
        <div class="chat-message-row ai">
            <div class="chat-message" style="overflow: hidden;">
                <div class="chat-message-txt">
                    <p><b>Bem vindo! Temos aqui algumas perguntas pré-definidas. Se desejar submetê-las clique no ícone de enviar ao lado de cada uma.</b></p>
                    <ul>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-1"></i> <span id="msg-default-1" >Resuma detalhadamente a petição inicial indicando os principais argumentos e pedidos</span></li>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-2"></i> <span id="msg-default-2">Resuma detalhadamente a contestação indicando os principais argumentos e pedidos</span></li>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-3"></i> <span id="msg-default-3">Resuma detalhadamente a sentença  indicando os principais argumentos e a decisão final</span></li>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-4"></i> <span id="msg-default-4">Resuma detalhadamente o recurso indicando os principais argumentos e pedidos</span></li>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-5"></i> <span id="msg-default-5">Resuma detalhadamente o acórdão indicando os principais argumentos e a decisão final</span></li>
                        <li><i class="btn-send-fake fa-solid fa-paper-plane" data-id="msg-default-6"></i> <span id="msg-default-6">Resuma detalhadamente o todos processo indicando as principais informações da petição inicial - contestação - sentença - recurso - acórdão -  indicando a página de cada de forma que seja possível acessar facilmente</span></li>
                    </ul>
                </div>
            </div>
        </div>
    `
    listMessagesEl.append(fakeConversation)

    mensagens.forEach((e) => appendConversation(e))
    showLatestMessage()

}

function clearChat() {
    listMessagesEl.empty()
    pdfContainer.empty()
}

function updateChatList(data, type) {
    if(type === 'add') {
        $('.choice-link-chat').removeClass('btn-info')
        listChatsEl.append(`<div class="choice-link-chat btn btn-info" data-id="${data.id}">${data.titulo}</div>`)
    }
    if(type === 'remove') {
        const option = listChatsEl.find(`div[data-id='${data}']`)
        option.remove()
        clearChat()
    }
}

function newChat(target) {
    const file = target.files[0]
    const formData = new FormData()
    formData.append('titulo', file.name)
    formData.append('documento', file)
    formData.append('ativo', true)

    const STATUS_OCR_FILA = 1
    formData.append('status', STATUS_OCR_FILA)

    if(validateDocument(documentType, target)) {
        if(isValidSizes(maxFileSizePdf, file)) {
            $.ajax({
                type:'POST',
                url: `/documento/api/chat/`,
                data: formData,
                contentType: false,
                processData: false,
                beforeSend:() => loader.fadeIn(),
                success: (data) => {
                    Swal.fire({
                        icon: "success",
                        title: 'Recebemos seu PDF!',
                        text: 'Iniciaremos em breve o processamento do seu PDF para extrair o máximo de informações e usá-las na nossa inteligência artificial. Você pode acompanhar o andamento desse processo na nossa Dashboard!',
                        confirmButtonColor:'#00c0ef'
                    }).then(() => {
                        window.location.href = `/documento/martinha/`
                    });
                },
                error: (error) => {
                    const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer a solicitação."
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
    } else {
        Swal.fire({
            icon: "error",
            title: "Tipo de arquivo não suportado",
            confirmButtonColor:'#00c0ef'
        }).then(() => {
            window.location.reload()
        });
    }
}

function getChat(chatId) {
    if(chatId) {
        $.ajax({
            type: 'GET',
            url: `/documento/api/chat/${chatId}/?criado_por=${userId.val()}&ativo=true`,
            success: (data) => fillChat(data),
            error: (erro) => console.log(erro)
        })
    } else {
        $.ajax({
            type: 'GET',
            url: `/documento/api/chat/?criado_por=${userId.val()}&ativo=true&status__in=4,8`,
            success: (data) => { 
                const { results } = data
                if(results.length) {
                    fillChat(results[0])
                } else {
                    clearChat()
                }
            },
            error: (erro) => clearChat()
        })
        
    }
}

function deleteChat(chatId) {
    if(chatId) {
        $.ajax({
            type: 'PATCH',
            url: `/documento/api/chat/${chatId}/`,
            data: {
                ativo: false
            },
            success: (data) => {
                updateChatList(chatId, 'remove')
            },
            error: () => {}
        })
    }
}

function resetChat(chatId) {
    if(chatId) {
        loader.fadeIn()
        $.ajax({
            type: 'GET',
            url: `/documento/api/chat/${chatId}/resetar_chat/`,
            success: (data) => {
                console.log(data)
            },
            error: () => {},
            complete: () => {
                loader.fadeOut()
                getChat(chatId)
            }
        })
    }
    
}

function appendConversation(askMsg, loading=true) {
    const getAutor = (autor) => {
        const autores = { 1: 'human', 2: 'ai' }
        return autores[autor] 
    }
    const getFavoriteMSG = () => {
        if(askMsg.id && askMsg.autor === 1) {
            return `<i data-id='${askMsg.id}' style='cursor:pointer;' data-favorito='${(askMsg.is_favorito)}' class='fa-${(askMsg.is_favorito) ?  'solid' : 'regular'}  fa-star salvar-favoritos'></i>`
        }
        return ''
    }

    const getClipboardAction = (askMsg) => {
        if(askMsg.id && askMsg.autor === 2) {
            return `<div class="clipboard-btn-container" data-toggle="tooltip" data-placement="left" title="Copiar" ><i class="fa-regular fa-clipboard clipboard-btn" data-clipboard-target="#message-${askMsg.id}"></i></div>`
        }
        return ''
    }

    var regex = /\[P(\d+)\]/g;

    let textoFormatado = askMsg.texto.replaceAll('\n', '<br>')

    textoFormatado = textoFormatado.replace(regex, function(match, numero) {
        return `<span class="btn-page" data-page="${numero}">${numero}</span>`;
    });

    let row = `
            <div class="chat-message-row ${getAutor(askMsg.autor)}">
                <div class="chat-message" style="overflow: hidden;">
                    ${getClipboardAction(askMsg)}
                    <div class="chat-message-txt" id="message-${askMsg.id}"><div> ${textoFormatado}</div> </div>
                </div>
            </div>
        `
    
    listMessagesEl.append(row)
    let cmr = document.querySelectorAll('.chat-message-txt')
    regex = 
    cmr.forEach(e=>{
        e.innerHTML = e.innerHTML.replace(/(\d+\.)\s(.*?:)/g, (match, p1, p2) => `<b>${p1}${p2}</b>`);
        e.innerHTML = e.innerHTML.replace(/(-+)\s(.*?:)/g, (match, p1, p2) => `${p1}<b>${p2}</b>`);
    })
}

function removeLoading() {
    $('#list-messages .fa-spinner').parent().parent().parent().remove()
}

function showLatestMessage() {
    const conversation = document.querySelector('#conversation')
    const messages = conversation.querySelectorAll('.chat-message-row')
    messages[messages.length -1].scrollIntoView()
}

function sendAsk(texto) {
    const data = {
        chat: chatIdOpenEl.val(),
        texto: texto,
        autor: 1
    }

    if(texto) {
        $.ajax({
            type:'POST',
            url: `/documento/api/mensagem/`,
            data: data, 
            beforeSend:() => {
                btnSendAsk.prop("disabled", true);
                appendConversation(data)
                appendConversation({
                    autor: 2,
                    texto: "<i class='fa-solid fa-spinner fa-spin'></i>"
                })
                showLatestMessage()
            },
            success: (response) => {
                removeLoading()
                appendConversation(response, false)
                prepareActionsChat() 
            },
            error: (error) => {
                const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."
                removeLoading()
                Swal.fire({
                    icon: "error",
                    title: mensagem,
                    confirmButtonColor:'#00c0ef'
                });
            },
            complete: () => {
                showLatestMessage()
                btnSendAsk.prop("disabled", false);
            }
        })
    }
}

function saveQuestion(id, is_favorito){
    const data = {
        is_favorito: !(is_favorito === 'true')
    }
    if(id) {
        $.ajax({
            type:'PATCH',
            url: `/documento/api/mensagem/${id}/`,
            data: data, 
            success: (response) => {
                console.log(response)
            },
            error: () =>  removeLoading(),
            complete: () => {
                // showLatestMessage()
                // btnSendAsk.prop("disabled", false);
            }
        })
    }
}

function getQuestion(id,question){
    if (question.trim().length > 0) {
        fetch(`/documento/api/mensagem/?criado_por=${id}&is_favorito=true&texto__icontains=${question}`)
        .then(res=>res.json())
        .then(data=>{
            const questions = data.results.reduce((acc,d) => {
                acc += `<li class='question'>${d.texto}</li>`
                return acc
            },'')

            if (questions.length > 0){
                questionBox.classList.remove('hide')
                listaQuestion.html(questions)
            }else{
                listaQuestion.html('')
                questionBox.classList.add('hide')
            }
            
        })
    } else{
        listaQuestion.html('')
        questionBox.classList.add('hide')

    }
}

function prepareActionsChat () {
    const menuActions = `
        <div id="chat-header-actions">
            <a href="/documento/export-chat-txt/${chatAtual.id}"><i class="fa-solid fa-download" data-toggle="tooltip" data-placement="bottom" title="Exportar chat"></i></a>
            <i id="reset-conversation" class="fa-solid fa-rotate-left" data-toggle="tooltip" data-placement="bottom" title="Resetar Chat"></i>
            <i id="remove-conversation" class="fa-solid fa-trash" data-toggle="tooltip" data-placement="bottom" title="Deletar Chat"></i>
        </div>
    `
    chatHeaderActions.html(menuActions)
    
    $("#remove-conversation").click(() => deleteChat(chatAtual.id))
    $("#reset-conversation").click(() => resetChat(chatAtual.id))

    const clipboard = new ClipboardJS('.clipboard-btn');

    clipboard.on('success', function(e) {
        const el = e.trigger
        e.clearSelection();
        el.classList.remove('fa-clipboard')
        el.classList.add('fa-square-check')

        setTimeout(() => {
            el.classList.remove('fa-square-check')
            el.classList.add('fa-clipboard')
        }, 2000)
    });

    $('[data-toggle="tooltip"]').tooltip()
}


function updateVisualizado(id) {
    if(id) {
        $.ajax({
            type: 'PATCH',
            url: `/documento/api/chat/${id}/`,
            data: {
                visualizado: true
            },
        })
    }
}
