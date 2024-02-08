const userId = $('#input-navbar-user-id').val()

$(function() {
    $(document).on('click', '.notifications-menu .dropdown-menu', function (e) {
        e.stopPropagation();
    });
    
    obterLembretesRecebidos();
    obterLembretesEnviados();
    handlePreferencias()
})

function obterLembretesRecebidos() {
    const listaLembretesElRef =  $('#lista-lembretes-recebidos')
    const lblCountLembreteElRef = $('#count-lembretes-recebidos')
    const tituloTotalLembretesRecebidosElRef = $('#titulo-total-lembretes-recebidos')
    $.ajax({
        url: `/lembrete/api/lembretes/`,
        data: {
            destinatario__id: userId,
            status__in:'1,2',
            lembrete_proprio: false
        },
        type: 'GET',
        success: (data) => {
            const results = data?.results || []
            const params = {
                lembretes: results, 
                msg: null, 
                listaLembretesElRef: listaLembretesElRef, 
                lblCountLembreteElRef: lblCountLembreteElRef, 
                tituloTotalLembretesElRef: tituloTotalLembretesRecebidosElRef
            }
            populaLembretes(params)
        },
        error: (error) => {
            const params = {
                lembretes: null, 
                msg: 'Não foi possivel obter os lembretes.', 
                listaLembretesElRef: listaLembretesElRef, 
                lblCountLembreteElRef: lblCountLembreteElRef, 
                tituloTotalLembretesElRef: tituloTotalLembretesRecebidosElRef
            }
            populaLembretes(params)
        }
    });
}

function obterLembretesEnviados() {
    const listaLembretesElRef =  $('#lista-lembretes-enviados')
    const lblCountLembreteElRef = $('#count-lembretes-enviados')
    const tituloTotalLembretesEnviadosElRef = $('#titulo-total-lembretes-enviados')
    $.ajax({
        url: `/lembrete/api/lembretes/`,
        data: {
            criado_por__id: userId,
            status__in:'1,2' ,
            lembrete_proprio: true
        },
        type: 'GET',
        success: (data) => {
            const results = data?.results || []
            const params = {
                lembretes: results, 
                msg: null, 
                listaLembretesElRef: listaLembretesElRef, 
                lblCountLembreteElRef: lblCountLembreteElRef, 
                tituloTotalLembretesElRef: tituloTotalLembretesEnviadosElRef
            }
            populaLembretes(params)
        },
        error: (error) => {
            const params = {
                lembretes: null, 
                msg: 'Não foi possivel obter os lembretes.', 
                listaLembretesElRef: listaLembretesElRef, 
                lblCountLembreteElRef: lblCountLembreteElRef, 
                tituloTotalLembretesElRef: tituloTotalLembretesEnviadosElRef
            }
            populaLembretes(params)
        }
    });
}

function obterLabelData(data) {
    if(data) {
        const dataLembrete = moment(data, 'YYYY-MM-DD').startOf('day')
        const hoje = moment().startOf('day');
        
        if(hoje.diff(dataLembrete, 'days') == 0) {
            return `<span>Hoje</span>`;
        } else if (dataLembrete < hoje) {
            return `<span> ${hoje.diff(dataLembrete, 'days')} dia(s) em atraso </span>`;
        } else {
            return `<span> Falta(m) ${dataLembrete.diff(hoje, 'days')} dia(s) </span>`;
        }
    } else {
        return `<span>Sem data</span>`;
    }
}

function populaLembretes({lembretes, msg, listaLembretesElRef, lblCountLembreteElRef, tituloTotalLembretesElRef}) {
    
    const corIcone = (prioridade) => {
        const tipos = {
            1: 'text-green',
            2: 'text-yellow',
            3: 'text-red'
        }
        return (tipos[prioridade] || tipos[1])
    }

    let listaEl  = '<ul class="menu">'

    if(lembretes && lembretes.length) {
        const totalPendentes = lembretes.filter((e) => [1,2].includes(e.status)).length
        if (lblCountLembreteElRef) lblCountLembreteElRef.text(totalPendentes || '')
        if (totalPendentes > 0) lblCountLembreteElRef.addClass('fa-beat')
        tituloTotalLembretesElRef.text(`(${lembretes.length})`)

        lembretes.forEach((l) => {
            listaEl += `<li>
                            <span  data-toggle="tooltip" data-placement="top" title="Clique para marcar como finalizado" onclick="finalizarLembrete(${l.id})" class="glyphicon glyphicon-unchecked ${corIcone(l.prioridade)}"></span>
                            <div class="bloco-lembrete-principal">
                                <a href="/admin/lembrete/lembretes/${l.id}/change/">${l.titulo}</a> 
                                <div class="lembrete-principal-infos">
                                    ${obterLabelData(l.data)}  
                                    ${(l.status == 1) ? '<span class="lbl-new">não visualizado</span>' : ''}
                                    ${l.documento ? `<a href=${l.documento} target="_blank" data-toggle="tooltip" data-placement="top" title="Visualizar documento"><i class='fa-solid fa-cloud-arrow-down' style="color:#00c0ef"></i></a>`: ''}
                                </div>
                            </div>
                        </li>`
        })
    } else if(msg) {
        listaEl +=  `<li><span class="msg-aviso">${msg}</span></li>`
        if (lblCountLembreteElRef) lblCountLembreteElRef.text('')
        tituloTotalLembretesElRef.text(`(0)`)
    } else {
        listaEl += `<li><span class="msg-aviso">Nenhum lembrete pendente.</span></li>`
        if (lblCountLembreteElRef) lblCountLembreteElRef.text('')
        tituloTotalLembretesElRef.text(`(0)`)
    }

    listaEl += '</ul>'

    listaLembretesElRef.html(listaEl)
}

function fecharSnackbarLembrete() {
    $('#snackbar-lembrete').removeClass('show')
}

function mostrarSnackbarLembrete() {
    $('#snackbar-lembrete').addClass('show')
}

let ultimoLembreteFinalizado = null;

function desfazerFinalizarLembrete() {
    const STATUS_VISUALIZADO = 2
    
    fecharSnackbarLembrete()

    if(ultimoLembreteFinalizado) {
        $.ajax({
            url: `/lembrete/api/lembretes/${ultimoLembreteFinalizado}/`,
            type: 'PATCH',
            data: {'status': STATUS_VISUALIZADO},
            complete: () => {
                obterLembretesRecebidos();
                obterLembretesEnviados();
            }
        });
    }
}

function finalizarLembrete(id) {
    const STATUS_FINALIZADO = 4;

    fecharSnackbarLembrete();

    $.ajax({
        url: `/lembrete/api/lembretes/${id}/`,
        type: 'PATCH',
        data: {'status': STATUS_FINALIZADO},
        complete: () => {
            obterLembretesRecebidos();
            obterLembretesEnviados();

            ultimoLembreteFinalizado = id;
            mostrarSnackbarLembrete();
        }
    });
}

// timer de 60 min

var tempoInicial = 60;

var tempoMilissegundos = tempoInicial * 60 * 1000;

function atualizarContador() {
    if (document.hasFocus()){
        var minutos = Math.floor(tempoMilissegundos / 1000 / 60);
        var segundos = Math.floor((tempoMilissegundos % (1000 * 60)) / 1000);
    
        minutos = minutos < 10 ? "0" + minutos : minutos;
        segundos = segundos < 10 ? "0" + segundos : segundos;
        document.getElementById("logoutTimer").textContent = ` ${minutos}:${segundos}`;
    
        tempoMilissegundos -= 1000;
    
        if (tempoMilissegundos < 0) {
           window.location.href = '/admin/logout' 
        }
    }
}

var contadorInterval = setInterval(atualizarContador, 1000);

function reiniciarContador() {
    document.getElementById("logoutTimer").textContent = " 60:00";
    clearInterval(contadorInterval);
    tempoMilissegundos = tempoInicial * 60 * 1000;
    contadorInterval = setInterval(atualizarContador, 1000);
}
  
document.addEventListener("mousemove", reiniciarContador);



/* ================================ Preferências do usuário =====================================  */

function handlePreferencias() {

    function blockCheckPreferencias(bool){
        $('#checkbox-liga-abas').attr('disabled',bool);
        $('.check_preferencia').attr('disabled',bool);

        (bool) ? $('.spin-preferencias').fadeIn() : $('.spin-preferencias').fadeOut();
        
        if (!bool) alert('Erro ao salvar as preferências do usuário')
    }
    
    $('#checkbox-liga-abas').change(() => {
        let value = $('#checkbox-liga-abas').is(":checked")
        salvarPreferenciaAba(value)
    })

    $('#checkbox-liga-abas-perfil').change(() => {
        let value = $('#checkbox-liga-abas-perfil').is(":checked")
        salvarPreferenciaAba(value)
    })

    function salvarPreferenciaAba(value){
        if(value !== undefined) {
            $.ajax({
                url: `/app-assistido/api/user/${userId}/`,
                type: 'PATCH',
                data: {'preferencia_abas': value},
                beforeSend: () => {
                    blockCheckPreferencias(true)
                },
                success: (data) => {
                    window.location.reload();
                },
                error: () => {
                    blockCheckPreferencias(false)
                },
            });
        }
    }
    
    $('.check_preferencia').change((e) => {
        const el = $(e.target)
        let checked = el.is(":checked")
        
        let preferencia = el.attr('data-preferencia')
        let id = el.attr('data-id')
        const preferenciaTelaAntiga = '2'
        
        const redirect = () => {
            if(preferencia === preferenciaTelaAntiga) {
                
                const pathName = window.location.pathname
                const pathTelaNova = '/atendimento/assistido-processo/processo-visualizar/'
                const pathTelaAntiga = '/admin/atendimento/processos/'
                
                if(checked && pathName.includes(pathTelaNova) ) {
                    let id = pathName.replace(pathTelaNova, '').split('/')[0]
                    if(id) {
                        window.location.href = `${pathTelaAntiga}${id}/`
                        return
                    }
                }
                if(!checked && pathName.includes(pathTelaAntiga) ) {
                    let id = pathName.replace(pathTelaAntiga, '').split('/')[0]
                    if(id) {
                        window.location.href = `${pathTelaNova}${id}/0/`
                        return
                    }
                }
            }
            window.location.reload();
        }

        if(checked !== undefined) {
            if(checked) {
                $.ajax({
                    url: `/users/api/user-preferencias/`,
                    type: 'POST',
                    data: {
                        'user': userId,
                        'preferencia': parseInt(preferencia)
                    },
                    beforeSend: () => {
                        blockCheckPreferencias(true)
                    },
                    success: (data) => {
                       redirect()
                    },
                    error: () => {
                        blockCheckPreferencias(false)
                    }
                });
            } else {
                if(id) {
                    $.ajax({
                        url: `/users/api/user-preferencias/${id}`,
                        type: 'DELETE',
                        beforeSend: () => {
                            blockCheckPreferencias(true)
                        },
                        success: (data) => {
                            redirect()
                        },
                        error: () => {
                            blockCheckPreferencias(false)
                        }
                    });
                }
            }
        }
    })
}