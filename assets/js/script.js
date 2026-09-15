document.addEventListener("DOMContentLoaded", function() {
    // =======================================================
    // 1. CAPTURA DE ELEMENTOS DO DOM
    // =======================================================
    const radioSim = document.getElementById('anonimo-sim');
    const radioNao = document.getElementById('anonimo-nao');
    const formDenuncia = document.getElementById('form-denuncia');
    const checkboxBoaFe = document.getElementById('boa-fe');
    
    // Elementos de arquivo
    const inputArquivo = document.getElementById('arquivo');
    const listaArquivos = document.getElementById('lista-arquivos');
    const dataTransfer = new DataTransfer(); // Nosso "cofre" que acumula arquivos

    // =======================================================
    // 2. ESCUTADORES DE EVENTO (ANONIMATO)
    // =======================================================
    if (radioSim && radioNao) {
        radioSim.addEventListener('change', gerenciarAnonimato);
        radioNao.addEventListener('change', gerenciarAnonimato);
        
        // Garante que a regra rode assim que a página terminar de carregar
        gerenciarAnonimato(); 
    }

    // =======================================================
    // 3. VALIDAÇÃO DO FORMULÁRIO (BOA-FÉ)
    // =======================================================
    if (formDenuncia) {
        formDenuncia.addEventListener('submit', function(evento) {
            if (!checkboxBoaFe.checked) {
                evento.preventDefault();
                alert('Para prosseguir, você deve aceitar o Termo de ciência e comprometimento.');
            }
        });
    }

    // =======================================================
    // 4. ACÚMULO, EXIBIÇÃO E EXCLUSÃO DE ARQUIVOS
    // =======================================================
    
    // Função responsável por desenhar a lista na tela e sincronizar com o input
    function atualizarListaArquivos() {
        listaArquivos.innerHTML = ''; // Limpa a lista visual para redesenhar
        
        for (let i = 0; i < dataTransfer.files.length; i++) {
            let li = document.createElement('li');
            li.style.marginBottom = "8px";
            li.style.display = "flex";
            li.style.alignItems = "center";
            li.style.fontSize = "14px";
            
            // Nome do arquivo
            let nomeArquivo = document.createElement('span');
            nomeArquivo.innerText = '📎 ' + dataTransfer.files[i].name;
            nomeArquivo.style.marginRight = "15px";
            
            // Botão de excluir
            let btnRemover = document.createElement('button');
            btnRemover.type = "button";
            btnRemover.innerHTML = "✖ Remover";
            btnRemover.style.background = "#ffebee";
            btnRemover.style.color = "#c62828";
            btnRemover.style.border = "none";
            btnRemover.style.padding = "4px 8px";
            btnRemover.style.borderRadius = "4px";
            btnRemover.style.cursor = "pointer";
            btnRemover.style.fontSize = "11px";
            btnRemover.style.fontWeight = "bold";
            
            // O que acontece quando clica em remover
            btnRemover.onclick = function() {
                dataTransfer.items.remove(i); // Remove do cofre pela posição (índice)
                atualizarListaArquivos(); // Redesenha a lista atualizada
            };

            li.appendChild(nomeArquivo);
            li.appendChild(btnRemover);
            listaArquivos.appendChild(li);
        }
        
        // Sincroniza os arquivos que sobraram no cofre com o formulário oficial
        if (inputArquivo) {
            inputArquivo.files = dataTransfer.files;
        }
    }

    if (inputArquivo && listaArquivos) {
        inputArquivo.addEventListener('change', function(e) {
            // Adiciona os novos arquivos ao cofre
            for (let i = 0; i < this.files.length; i++) {
                dataTransfer.items.add(this.files[i]);
            }
            
            // Limpa o input original para permitir selecionar o mesmo arquivo de novo caso tenha sido excluído
            this.value = ''; 
            
            atualizarListaArquivos();
        });
    }
});

// =======================================================
// 5. FUNÇÃO PARA EXIBIR/OCULTAR IDENTIFICAÇÃO (ANIMAÇÃO E VALIDAÇÃO)
// =======================================================
function gerenciarAnonimato() {
    const divIdentificacao = document.getElementById('campos-identificacao');
    const radioSim = document.getElementById('anonimo-sim');

    if (divIdentificacao && radioSim) {
        // Seleciona todos os inputs e selects dentro da aba de dados pessoais
        const camposPessoais = divIdentificacao.querySelectorAll('input, select, textarea');

        if (radioSim.checked) {
            // MODO ANÔNIMO: Esconde a div com animação
            divIdentificacao.style.opacity = '0';
            setTimeout(() => {
                divIdentificacao.style.display = 'none';
            }, 300);

            // Tira a obrigatoriedade e limpa os campos escondidos
            camposPessoais.forEach(campo => {
                campo.required = false;
                campo.value = ''; 
            });
        } else {
            // MODO IDENTIFICADO: Mostra a div com animação
            divIdentificacao.style.display = 'block';
            setTimeout(() => {
                divIdentificacao.style.opacity = '1';
            }, 10);

            // Torna os campos de identificação obrigatórios
            camposPessoais.forEach(campo => {
                campo.required = true;
            });
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    const inputChat = document.getElementById('input-arquivo-chat');
    const listaChat = document.getElementById('lista-arquivos-chat');
    let arquivoChat = null; // Guardamos apenas um arquivo por mensagem

    if (inputChat) {
        inputChat.addEventListener('change', function() {
            if (this.files.length > 0) {
                arquivoChat = this.files[0];
                listaChat.innerHTML = `
                    <li style="font-size: 12px; color: #555; margin-top: 5px;">
                        📎 ${arquivoChat.name} 
                        <button type="button" onclick="limparAnexoChat()" style="border:none; background:none; color:red; cursor:pointer;">(Remover)</button>
                    </li>
                `;
            }
        });
    }
});

function limparAnexoChat() {
    document.getElementById('input-arquivo-chat').value = '';
    document.getElementById('lista-arquivos-chat').innerHTML = '';
}

// =======================================================
// 6. MÁSCARA DE TELEFONE
// =======================================================
document.addEventListener("DOMContentLoaded", function() {
    const inputTelefone = document.getElementById('telefone');

    if (inputTelefone) {
        inputTelefone.addEventListener('input', function(e) {
            // Pega o valor atual e remove tudo que não for número
            let valor = e.target.value.replace(/\D/g, "");
            
            // Aplica a formatação (DD) 9XXXX-XXXX ou (DD) XXXX-XXXX
            valor = valor.replace(/^(\d{2})(\d)/g, "($1) $2");
            valor = valor.replace(/(\d)(\d{4})$/, "$1-$2");
            
            // Atualiza o campo com o valor formatado
            e.target.value = valor;
        });
    }
});

// Variável que funciona como um "cadeado" para a caixa de seleção
let termoLido = false;
const checkboxTermo = document.getElementById('boa_fe');

if (checkboxTermo) {
    checkboxTermo.addEventListener('click', function(evento) {
        if (!termoLido) {
            // Impede a caixinha de ficar marcada
            evento.preventDefault(); 
            
            // Avisa o usuário e abre o pop-up de regras automaticamente
            alert("Para marcar esta opção, você precisa ler as regras primeiro. Clique em 'OK' para visualizar o termo.");
            abrirModal(evento); 
        }
    });
}

// =========================================
// Funções do Pop-up (Termo de Ciência)
// =========================================
function abrirModal(evento) {
    if (evento) {
        evento.preventDefault(); 
        evento.stopPropagation(); 
    }
    
    // Abre a tela escura com as regras
    document.getElementById('modal-termo').style.display = 'flex';
    
    // Libera o acesso: assim que o modal abre, o cadeado é destrancado
    termoLido = true;
}

function fecharModal() {
    document.getElementById('modal-termo').style.display = 'none';
}

// Fecha o pop-up se o usuário clicar fora da área branca
window.onclick = function(event) {
    const modal = document.getElementById('modal-termo');
    if (event.target === modal) {
        fecharModal();
    }
};