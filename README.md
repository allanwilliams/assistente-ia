![Alt text](/static/logo-vertical-novo-modelo.png)
# Template Django Admin
Supported by✨COTIN✨

Esse é um template base para criação de novos projetos baseados em Django Admin. Após clonar o repositório a pasta .git deverá ser deletada antes de inciar o desenvolvimento.
## Tecnologias

- [Django](https://www.djangoproject.com/) - Verison 3.2.7
- [Python](https://www.python.org/) - version 3.8.*

## TEMAS

Esse template possui 2 temas previamente configurados

- AdminLTE
- Django-jazzmin

para escolher entre eles basta incluir o parâmetro DEFAULT_THEME em sua .env, caso o parâmetro não seja incluido o tema AdminLTE será utilizado por padrão


.env
```
DEFAULT_THEME=jazzmin.apps.JazzminConfig # para habilitar o tema Django-jazzmin
DEFAULT_THEME=adminlteui.apps.AdminlteUIConfig # para habilitar o tema AdminLTE
```

## Instalação
Instale o Virtualenv, certifique-se de estar dentro da pasta do projeto ...
```sh
 cd pasta-do-projeto
 ```

Crie a Virtualenv ...
```sh
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências da venv ...
```sh
pip install -r requirements.txt
```

Configurando a .env
```sh
cp .env_exemplo .env
```

### Instalando WKHTMLTOPDF no CentoOS7

```
yum install fontconfig libXext freetype libpng zlib libjpeg-turbo libpng libjpeg openssl icu libX11 libXext libXrender xorg-x11-fonts-Type1 xorg-x11-fonts-75dpi
sudo yum install -y https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox-0.12.5-1.centos7.x86_64.rpm
```

### Instalação Font Arial
```
sudo apt install ttf-mscorefonts-installer
sudo fc-cache -f
fc-match Arial

```

## Integração com FusionAuth

Caso deseje utilizar o FusionAuth os parametros abaixo deverão ser configurados na .env
```
[FUSIONAUTH_HOST]: Endereço do servidor do FusionAuth ex: http://127.0.0.1:9011/
[USE_FUSIONAUTH]: Flag que habilita a integração (se for False a autenticação será feita usando Django Admin convencional)
[FUSIONAUTH_USER_API_KEY]: Chave de segurança para a API de User do FusionAuth
[OIDC_RP_CLIENT_ID]: ID gerado para a aplicação no FusionAuth
[OIDC_RP_CLIENT_SECRET]: SECRET gerado para a aplicação no FusionAuth
```

A classe User possui um recurso que possibilita compartilhar informações com o FusionAuth, onde campos da model podem ser gravados diretamente na base de dados do FusionAuth.

Para configurar campos compartilhados basta adiciona-los na funcao userdata_list_fields
ex:
```
    def userdata_list_fields(self):
        return [
            'cpf','campo1','campo2'
        ]
```
## Padrões de Roles FusionAuth
Sempre que uma nova application for inicializada no FusionAuth as roles de controle deverão ser criadas
```
FLAG[IS_ADMIN]: Garante acesso administrativo ao usuário dentro do ambiente da aplicação
FLAG[IS_STAFF]: Garante acesso ao usuário dentro do ambiente da aplicação
```

- Configuração de Papeis

As roles de papel deverão possuir a palavra chave PAPEL(caixa alta) e o nome do papel dentro de [] (cochetes). Dessa forma o django_sso_app irá reconhecer o papel do usuário e atualiza-lo corretamente. 
Obs: Somente uma role de Papel poderá ser habilitada por usuário na Aplicação, caso mais de uma seja habilitada a ultima role é que valerá.

exemplo:
```
PAPEL[Colaborador(a)]
```

- Configurações de Grupos

As roles de grupo deverão possuir a palavra chave GRUPO(caixa alta) e o nome do grupo (Exatamente como está cadastrado no sistema) dentro de "[]" (cochetes)

exemplo:
```
GRUPO[Defensores]
```

## Testes
Antes de iniciar os testes habilite a venv
```
source venv/bin/activate
```
Executando todos dos testes

```
coverage run --omit="*/venv/*,config/*,static/*,staticfiles/*,adminlteui/*,jazzmin/*" manage.py test apps --settings config.cicd_settings;coverage html --omit="*/venv/*,config/*,static/*,staticfiles/*,adminlteui/*,jazzmin/*" -d tests/coverage; coverage xml -i
```

Executando testes por app

```
coverage run manage.py test apps/{nome_do_app}; coverage html --omit="*/venv/*,config/*,static/*,staticfiles/*,adminlteui/*,jazzmin/*" -d tests/coverage
```

Os resultados dos testes serão gravados na pasta tests/coverage/ e podem ser acessados abrindo o arquivo tests/coverage/index.html

## Criptografia
O template possui uma camada de criptografia centralizada aplicada a todas models que herdam de BaseModel. 

Para habilitar campos basta incluir os fields na propriedade crypted_fields da model
ex:

```
class Exemplo(BaseModel):
    campo_exemplo = models.CharField(max_length=500,null=True,blank=True)

    crypted_fields = ['campo_exemplo',]
```

obs: Os campos criptografados deverão ser do tipo ChatField e ter um max_length que permita gravar a hash gerada