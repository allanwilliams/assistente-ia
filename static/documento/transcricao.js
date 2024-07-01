const inputTxtAsk = $('#transcricao-input-ask')
const btnSendAsk = $("#btn-send-ask")
const listMessagesEl = $("#list-messages")
const transcricaoFormInput = $("#transcricao-form-input")
const transcricaoIdOpenEl = $('#transcricao-id-open')
const listTranscricoesEl = $('#list-Transcricoes')
const mediaContainer = $('#media-obj-container')
const body = document.querySelector('body')
const dropArea = document.querySelector(".drag-area")
const fileInput = dropArea.querySelector(".file-input")
const userId = $("#user-id")
const listaQuestion = $('#lista-question')
const questionBox = document.querySelector('#questionBox')
const loader = $("#preloader")
const btnFindText = document.querySelector('#btn-find-text')
const transcricaoInputAsk = document.querySelector('#transcricao-input-ask')
const colors = ['#179B14', '#BC1414', '#FA8C0B', '#000000', '#0DA78B', '#0D6FA7', '#510BAA', '#C20FC6', '#F2E03E', '#FF6384', '#4BC0C0', '#8D99AE']

let transcricaoAtual = null

body.addEventListener('click', function(event) {

    if(event.target.classList.contains('choice-link-transcricao')) {
        const transcricaoId = event.target.attributes['data-id'].value
        getTranscricao(transcricaoId)
    }

    if(event.target.classList.contains('btn-remove-transcricao')) {
        const transcricaoId = event.target.attributes['data-remove-id'].value
        deletetranscricao(transcricaoId)
    }

    if(event.target.classList.contains('btn-go-to-time')) {
        const time = event.target.attributes['data-time'].value
        goToTime(time)
    } 
    if(event.target.classList.contains('btn-go-to-transcript')) {
        const time = event.target.attributes['data-time'].value
        const id = event.target.attributes['data-id'].value

        const el = $(`#message-${id} .text-msg`)
        $('.text-msg').removeClass('highlight')
        el.addClass('highlight')
        el[0].scrollIntoView({ block: "center", behavior: "smooth" })
        goToTime(time)
    }

    if(event.target.classList.contains('btn-edit-speaker')) {
        const msgId = event.target.attributes['data-id'].value
        const speaker = event.target.attributes['data-speaker'].value
        const colorSpeaker = event.target.attributes['data-color-speaker'].value
        const replaceAllDefault = event.target.attributes['data-replace-all-default'].value === 'true'

        openDialogEditSpeaker(msgId, speaker, colorSpeaker, replaceAllDefault)
    }

    if(event.target.classList.contains('vetar-transcricao')) {
        const id = event.target.attributes['data-id'].value
        const vetado = event.target.attributes['data-vetado'].value
        event.target.attributes['data-vetado'].value = !(vetado === 'true')
        saveVeto(id, vetado)

        const el = $(event.target).parent().siblings().first()
        if(el) {
            el.toggleClass('vetado')
        }
    }
    if(event.target.classList.contains('salvar-favoritos')) {
        const msgID = event.target.attributes['data-id'].value
        const favorito = event.target.attributes['data-favorito'].value
        event.target.attributes['data-favorito'].value = !(favorito === 'true')
        
        saveFavorite(msgID, favorito)

        const el = $(event.target).parent().siblings().first()
        
        if(el) {
            el.toggleClass('favoritado')
        }
        
        event.target.classList.remove('fa-solid')
        event.target.classList.remove('fa-regular')
        
        const CF = (val) => {
            event.target.classList.add(val)
        } 

        (favorito === 'true') ? CF('fa-regular') : CF('fa-solid');
    }
})

$(document).ready(() => {
    fileInput.accept = mediaTranscriptionTypes.join(',')

    dropArea.onclick = () => {
        fileInput.click();
    };
    fileInput.addEventListener("change", function (e) {
        const target = e.target;
        newtranscricao(target)
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
        newtranscricao(target)
    });
    
    if(userId.val()) {
        getUserTranscricoes(userId.val())
        .then((data) => data.json())
        .then((data) => fillListTranscricoes(data.results))
        .then(() => {
            const url = window.location.search
            const urlParams = new URLSearchParams(url);
            const documento = urlParams.get('arquivo')
            getTranscricao(documento)
        })
    }
})

function getUserTranscricoes(userId) {
    const STATUS_CONCLUIDO = 4
    return fetch(`/documento/api/media-transcricao/?criado_por=${userId}&ativo=true&status=${STATUS_CONCLUIDO}`)
}

function fillListTranscricoes(transcricoes) {
    let list = ''
    const STATUS_CONCLUIDO = 4

    transcricoes = transcricoes.filter(c => c.status === STATUS_CONCLUIDO )
    transcricoes.forEach((c) => {
       list += `<div class="choice-link-transcricao btn" data-id="${c.id}">${c.titulo}</div>`
    })

    listTranscricoesEl.html(list)
}

function filltranscricao(data) {
    const {id, transcricoes, titulo, arquivo, tipo, legenda, visualizado, status } = data
    loadDocumento(titulo, arquivo, id,tipo,legenda)
    insertConversation(transcricoes)
    transcricaoAtual = data
    transcricaoIdOpenEl.val(id)
    getFavoriteTranscriptions(transcricoes)
    getIndividualSpeakers(transcricoes)
    prepareActions()

    if(!visualizado && status === 4 ) {
        updateVisualizado(id)
    }

    let links = $('.choice-link-transcricao')
    links.removeClass('btn-info')

    let link = links.filter((i, e) => e.attributes['data-id'].value === id.toString())
    if(link.length > 0) {
        link[0].classList.add('btn-info')
    }
}


function loadDocumento(titulo, url, id, tipo, legenda) {
    let classe = 'audio'
    if (tipo == 1) { classe = 'video'}
    const newUrl = url.includes('http://martinha') || url.includes('http://tanaka') ? url.replace('http://','https://') : url
    const newLegendaUrl = legenda.includes('http://martinha') || legenda.includes('http://tanaka') ? legenda.replace('http://','https://') : legenda
    mediaContainer.html(`
        <div class="media-header">
            <h3 title="${titulo}">${titulo}</h3> 
            <div>
                <a href="/documento/export-transcricoes-txt/${id}"><i class="fa-solid fa-download" data-toggle="tooltip" data-placement="bottom" title="Exportar transcrição"></i></a>
                <i data-remove-id='${id}' class='fa fa-trash btn-remove-transcricao'></i>
            </div>
        </div>
        <video id="media-el" controls preload="auto" class="${classe}">
            <source src="${newUrl}" />
            <track label="Português" kind="subtitles" srclang="en" src="${newLegendaUrl}" default />
        </video>
        <div id="media-footer">
            <div id="favorite-transcriptions"></div>
            <div id="edit-group-speakers"></div>
        </div>
    `)
}

btnFindText.addEventListener('click',function(){
    const busca = transcricaoInputAsk.value
    destacarPorString(busca) 
})

transcricaoInputAsk.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    const busca = transcricaoInputAsk.value
    destacarPorString(busca)
  }
});

function destacarPorString(textoBusca) {
    textoBusca = textoBusca.trim()
    var mensagens = document.querySelectorAll('.text-msg');
    for(const mensagem of mensagens){
        
        var texto = mensagem.innerHTML;
        texto = texto.replace(/<span class="highlight">(.*?)<\/span>/g, '$1');
        var regex = new RegExp(textoBusca, 'gi'); // 'gi' para correspondência global e sem diferenciar maiúsculas e minúsculas
        var textoAtualizado = texto.replace(regex, function(match) {
            return '<span class="highlight">' + match + '</span>';
        });

        
        mensagem.innerHTML = textoAtualizado
    }

    const conversation = document.querySelector('#conversation')
    const messages = conversation.querySelectorAll('.highlight')
    if(messages.length) {
        messages[0].scrollIntoView({ block: "center", behavior: "smooth" })
    }
}

function insertConversation(transcricoes) {
    listMessagesEl.empty()

    transcricoes.forEach((e) => appendConversation(e))
}

function cleartranscricao() {
    listMessagesEl.empty()
    mediaContainer.empty()
}

function updatetranscricaoList(data, type) {
    if(type === 'add') {
        $('.choice-link-transcricao').removeClass('btn-info')
        listTranscricoesEl.append(`<div class="choice-link-transcricao btn btn-info" data-id="${data.id}">${data.titulo}</div>`)
    }
    if(type === 'remove') {
        const option = listTranscricoesEl.find(`div[data-id='${data}']`)
        option.remove()
        cleartranscricao()
    }
}

function newtranscricao(target) {
    const file = target.files[0]
    const tipo = audioTypes.indexOf(file.type) != -1 ? 2 : 1
    const formData = new FormData()
    formData.append('titulo', file.name)
    formData.append('arquivo', file)
    formData.append('ativo', true)
    formData.append('tipo', tipo)
    
    if(validateDocument(mediaTranscriptionTypes, target)) {
        if(isValidSizes(maxFileSizeMedia, file)) {
            $.ajax({
                type:'POST',
                url: `/documento/api/media-transcricao/`,
                data: formData,
                contentType: false,
                processData: false,
                beforeSend:() => loader.fadeIn(),
                success: (data) => {
                    Swal.fire({
                        icon: "success",
                        title: 'Recebemos seu arquivo!',
                        text: 'Iniciaremos em breve o processamento do seu arquivo para extrair o máximo de informações e usá-las na nossa inteligência artificial. Você pode acompanhar o andamento desse processo na nossa Dashboard!',
                        confirmButtonColor:'#00c0ef'
                    }).then(() => {
                        window.location.href = `/documento/tanaka/`
                    });
                },
                error: (error) => {
                    const mensagem = (error?.responseJSON?.mensagem) ? error?.responseJSON?.mensagem : "Houve um erro ao fazer o upload."
                    Swal.fire({
                        icon: "error",
                        title: mensagem,
                        confirmButtonColor:'#00c0ef'
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

function getTranscricao(transcricaoId) {
    if(transcricaoId) {
        $.ajax({
            type: 'GET',
            url: `/documento/api/media-transcricao/${transcricaoId}/?criado_por=${userId.val()}&ativo=true`,
            success: (data) => filltranscricao(data),
            error: (erro) => console.log(erro)
        })
    } else {
        $.ajax({
            type: 'GET',
            url: `/documento/api/media-transcricao/?criado_por=${userId.val()}&ativo=true&status=4`,
            success: (data) => {
                const { results } = data
                if(results.length) {
                    filltranscricao(results[0])
                } else {
                    cleartranscricao()
                }
            },
            error: (erro) => cleartranscricao()
        })
        
    }
}

function deletetranscricao(transcricaoId) {
    if(transcricaoId) {
        $.ajax({
            type: 'PATCH',
            url: `/documento/api/media-transcricao/${transcricaoId}/`,
            data: {
                ativo: false
            },
            success: (data) => {
                updatetranscricaoList(transcricaoId, 'remove')
            },
            error: () => {}
        })
    }
}

function appendConversation(askMsg, loading=true) {
    let textoFormatado = askMsg.texto.replaceAll('\n', '<br>')

    const getClipboardAction = (askMsg) => {
        return ``
    }

    let row = `
            <div class="transcricao-message-row">
                <div class="transcricao-message ${(askMsg.is_favorito) ? 'favoritado' : ''} ${askMsg.is_vetado ? 'vetado' : '' }" style="overflow: hidden;">
                    <div class='avatar' style="background-color:${askMsg.cor_speaker}">
                        <i class='fa fa-user'></i>
                    </div>
                    <div class="transcricao-message-txt" id="message-${askMsg.id}">
                        <div><strong style="margin-right:5px;">${askMsg.speaker}</strong> <i class="fa-solid fa-pen-to-square btn-edit-speaker" data-id="${askMsg.id}" data-speaker="${askMsg.speaker}" data-color-speaker="${askMsg.cor_speaker}" data-replace-all-default="" data-toggle="tooltip" data-placement="right" title="Editar orador"></i></div>
                        <div><i class="fa-solid fa-forward-step pointer btn-go-to-time" data-time=${askMsg.tempo_inicial_segundos} data-toggle="tooltip" data-placement="bottom" title="Ir para"></i> <strong>${askMsg.tempo_inicial} <i class='fa fa-arrow-right'></i> ${askMsg.tempo_final}</strong>: </div>
                        <div class='text-msg'><span>${textoFormatado}</span></div> 
                    </div>
                </div>
                <div class="clipboard-btn-container">
                    <i data-id='${askMsg.id}' data-favorito='${(askMsg.is_favorito)}' class='fa-${(askMsg.is_favorito) ?  'solid' : 'regular'}  fa-star salvar-favoritos'></i>
                    <i class="fa-regular fa-clipboard clipboard-btn" data-clipboard-target="#message-${askMsg.id}" data-toggle="tooltip" data-placement="left" title="Copiar"></i>
                    <i data-id='${askMsg.id}' data-vetado='${(askMsg.is_vetado)}' class='fa${(askMsg.is_vetado) ?  '-solid' : ''} fa-ban vetar-transcricao' data-toggle="tooltip" data-placement="left" title="${(askMsg.is_vetado) ? 'Reconsiderar' : 'Desconsiderar'} "></i>
                </div>
            </div>
        `
    
    listMessagesEl.append(row)
}

function removeLoading() {
    $('#list-messages .fa-spinner').parent().parent().parent().remove()
}

function showLatestMessage() {
    const conversation = document.querySelector('#conversation')
    const messages = conversation.querySelectorAll('.transcricao-message-row')
    messages[messages.length -1].scrollIntoView()
}

function openDialogEditSpeaker(id, speaker, colorSpeaker, replaceAllDefault) {
    const radioChecked = (color) => (colorSpeaker == color ? 'checked' : '' )

    Swal.fire({
        title: "Editar falante",
        html: `
            <div class="form-group">
                <label>Nome</label>
                <input class="form-control" id='name' type='text' value='${speaker}'>
            </div>
            <label>Cor do avatar</label>
            <div class="dialog-color-speaker">
                ${colors.map((c) => `
                    <div>
                        <input type="radio" name="color" value="${c}" id="${c}"  ${radioChecked(c)} />
                        <label class="radio-inline" for="${c}" style="background-color:${c};"></label>
                    </div>
                `).join('')}
            </div>
            <label>
                <input id="replace-all" type="checkbox" ${replaceAllDefault ? 'disabled checked' : ''}> Substituir em todos com o mesmo nome
            </label>
        `,
        showCancelButton: true,
        confirmButtonText: "Aplicar",
        cancelButtonText: 'Cancelar',
        confirmButtonColor:'#00c0ef',
        preConfirm: () => ({
           name: document.getElementById('name').value,
           color: document.querySelector('input[name="color"]:checked').value,
           replaceAll: document.getElementById('replace-all').checked,
        })
    }).then((result) => {
        if(result.isConfirmed) {
            const { name , replaceAll, color } = result.value
            updateSpeakerName({id, name, color, replaceAll})
        }
    })
}

function updateSpeakerName({id, name, color, replaceAll}) {
    $.ajax({
        type: 'PATCH',
        url: `/documento/api/transcricao/${id}/`,
        data: {
            speaker: name,
            cor_speaker: color,
            replaceAll
        },
        success: (data) => {
            if(transcricaoAtual) {
                getTranscricao(transcricaoAtual.id)
            }
        },
        error: () => {}
    })
}

function prepareActions () {
   
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

function goToTime(time) {
    const mediaEl = document.getElementById('media-el')
    mediaEl.currentTime = time
}

function getIndividualSpeakers(transcricoes) {
    let uniqueSpeakers = transcricoes.reduce((acc, curr) => {
        const currExists = acc.find((i) => i.speaker === curr.speaker)
        if(!currExists) acc.push(curr);

        return acc;
    },[])

    uniqueSpeakers.sort((a,b) => (a.speaker > b.speaker) ? 1 : ((b.speaker > a.speaker) ? -1 : 0))

    $('#edit-group-speakers').html(
        `
        <h3>Oradores da Transcrição</h3>
        <div class="edit-group-wrapper">
        <div class="edit-group-list">
            ${uniqueSpeakers.map((s) => `
                <div class="edit-group-item" style="background-color:${convertHexToRGBA(s.cor_speaker, 0.03)};">
                    <div class="avatar" style="background-color:${s.cor_speaker}">
                        <i class="fa fa-user"></i>
                    </div>
                    <span>${s.speaker}</span>
                    <i class="fa-solid fa-pen-to-square btn-edit-speaker" data-id="${s.id}" data-speaker="${s.speaker}" data-color-speaker="${s.cor_speaker}" data-replace-all-default="true"  data-toggle="tooltip" data-placement="right" title="Editar falante"></i>
                </div>
            `).join('')}
            
        </div>
        </div>
        `
    )
}

function saveFavorite(id, is_favorito) {

    const valueFavorito = !(is_favorito === 'true')
    if(id) {
        $.ajax({
            type:'PATCH',
            url: `/documento/api/transcricao/${id}/`,
            data: { is_favorito: valueFavorito }, 
            success: (response) => {
                if(transcricaoAtual) {
                    const index = transcricaoAtual.transcricoes.findIndex((i) => i.id === parseInt(id))

                    if(index !== -1) {
                        transcricaoAtual.transcricoes[index].is_favorito = valueFavorito
                    }
                    getFavoriteTranscriptions(transcricaoAtual.transcricoes)
                    $('.text-msg').removeClass('highlight')
                }
            },
            error: (e) =>  console.log(e),
        })
    }

}

function saveVeto(id, is_vetado) {

    const valueVetado = !(is_vetado === 'true')
    if(id) {
        $.ajax({
            type:'PATCH',
            url: `/documento/api/transcricao/${id}/`,
            data: { is_vetado: valueVetado }, 
            success: (response) => {
                // console.log(response)
            },
            error: (e) =>  console.log(e),
        })
    }
}

function getFavoriteTranscriptions(transcricoes) {
    const favorites = transcricoes.filter((t) => t.is_favorito)
   
    const getItems = () => {
        if(favorites.length) {
            const favoritesList = favorites.map((s) => `
                <div class="favorite-group-item">
                    <div><b>${s.speaker}</b></div>
                    <div class="group-item-text">${(s.texto.length > 50) ? `${s.texto.substring(0, 45)}...` : s.texto}</div>
                    <i class="fa-solid fa-eye pointer btn-go-to-transcript" data-id="${s.id}" data-time=${s.tempo_inicial_segundos} data-toggle="tooltip" data-placement="right" title="Ver"></i>
                </div>
            `).join('')

            return `<div class="favorite-group-list">${favoritesList}</div>`
            
        }
        return "<div class='empy-list'>Nenhum item favoritado ainda</div>"
    }

    $('#favorite-transcriptions').html(`<h3>Transcrições Favoritas <a href="/documento/export-transcricoes-txt/${transcricaoAtual.id}?favoritos=true"><i class="fa-solid fa-download" data-toggle="tooltip" data-placement="bottom" title="Exportar favoritos"></i></a></h3>${getItems()}`)
}

function updateVisualizado(id) {
    if(id) {
        $.ajax({
            type: 'PATCH',
            url: `/documento/api/media-transcricao/${id}/`,
            data: {
                visualizado: true
            },
        })
    }
}