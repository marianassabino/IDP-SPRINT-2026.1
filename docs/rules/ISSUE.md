# Implementar módulo de usuários e autenticação

## Contexto

O PRD define que o MVP deve permitir cadastro e login com email e senha, com 1 usuário por conta. O usuário precisa ter um espaço próprio para acessar seus projetos, configurações e dicionário global.

Esta issue cobre o módulo base de **Usuários e Autenticação**, necessário antes das funcionalidades de projetos, upload de planilhas, processamento e dicionário global.

## Objetivo

Criar autenticação segura usando:

- **JWT de acesso** para autenticar chamadas à API.
- **Cookies HTTP-only** para armazenar tokens sem expor ao JavaScript do frontend.
- **Refresh token** para renovar sessão sem obrigar login a cada expiração curta do access token.
- **Hash de senha** para nunca salvar senha em texto puro.
- **Arquitetura Clean/SOLID**, mantendo regras de negócio separadas de FastAPI, banco, JWT e cookies.

## Escopo

### Incluído

- Criar usuário com email e senha.
- Fazer login com email e senha.
- Gerar access token JWT.
- Gerar refresh token.
- Salvar refresh token de forma persistente e revogável.
- Enviar tokens em cookies seguros.
- Renovar access token usando refresh token.
- Fazer logout revogando o refresh token e limpando cookies.
- Endpoint para retornar o usuário autenticado atual.
- Endpoint para alterar senha do usuário autenticado.
- Middleware/dependência para proteger rotas privadas.
- Testes automatizados do fluxo principal.

### Fora do escopo

- Login social Google/Microsoft.
- SSO corporativo.
- Múltiplos usuários por conta.
- Permissões avançadas por papel.
- Recuperação de senha por email.
- Confirmação de email.

Esses itens estão fora do MVP conforme o PRD ou podem ficar para uma issue posterior.

## Decisões técnicas obrigatórias

### JWT

Usar JWT apenas para o **access token**.

O access token deve conter no payload, no mínimo:

```json
{
  "sub": "id-do-usuario",
  "type": "access",
  "iat": 1710000000,
  "exp": 1710000900
}
```

Regras:

- `sub` deve ser o ID do usuário.
- `type` deve diferenciar `access` de outros tokens.
- `exp` deve ser curto, sugestão: 15 minutos.
- Assinar com segredo vindo de variável de ambiente.
- Nunca aceitar token expirado.
- Nunca confiar em dados do payload sem validar assinatura e tipo.

### Cookies

Tokens devem ser enviados por cookie, não por body para o frontend guardar manualmente.

Cookies esperados:

- `access_token`
- `refresh_token`

Configuração mínima:

- `HttpOnly=true`
- `Secure=true` em produção
- `SameSite=Lax` no desenvolvimento e avaliar `Strict` em produção
- `Path=/`
- `Max-Age` compatível com expiração do token

Observação para o time:

`HttpOnly` impede que JavaScript leia o cookie. Isso reduz risco em caso de XSS. O navegador envia o cookie automaticamente nas próximas requisições.

### Refresh token

O refresh token deve permitir renovar a sessão sem pedir senha novamente.

Regras:

- Refresh token deve ter duração maior que o access token, sugestão: 7 dias.
- Refresh token deve ser salvo no banco com vínculo ao usuário.
- Não salvar refresh token puro no banco. Salvar hash do refresh token.
- Deve existir mecanismo para revogar refresh token no logout.
- Ao fazer refresh, gerar novo access token.
- Preferencialmente fazer rotação de refresh token: ao usar um refresh token válido, revogar o antigo e criar um novo.

## Endpoints esperados

### `POST /auth/register`

Cria usuário e já autentica.

Request:

```json
{
  "email": "usuario@email.com",
  "password": "senha-forte"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "usuario@email.com"
}
```

Efeitos:

- Cria usuário.
- Salva senha com hash.
- Gera access token.
- Gera refresh token.
- Define cookies `access_token` e `refresh_token`.

Validações:

- Email obrigatório e válido.
- Senha obrigatória.
- Email não pode estar duplicado.

### `POST /auth/login`

Autentica usuário existente.

Request:

```json
{
  "email": "usuario@email.com",
  "password": "senha-forte"
}
```

Response:

```json
{
  "id": "uuid",
  "email": "usuario@email.com"
}
```

Efeitos:

- Valida email e senha.
- Gera access token.
- Gera refresh token.
- Define cookies `access_token` e `refresh_token`.

Erros:

- Credenciais inválidas devem retornar erro genérico.
- Não informar se o email existe ou não.

### `POST /auth/refresh`

Renova sessão usando o cookie `refresh_token`.

Request:

- Sem body.
- Lê o refresh token do cookie.

Response:

```json
{
  "authenticated": true
}
```

Efeitos:

- Valida refresh token.
- Confirma que ele existe no banco e não foi revogado.
- Gera novo access token.
- Se houver rotação, gera novo refresh token e revoga o anterior.
- Atualiza cookies.

### `POST /auth/logout`

Encerra sessão.

Request:

- Sem body.
- Lê refresh token do cookie, se existir.

Response:

```json
{
  "authenticated": false
}
```

Efeitos:

- Revoga refresh token atual.
- Limpa cookies `access_token` e `refresh_token`.

### `GET /users/me`

Retorna o usuário autenticado.

Request:

- Usa cookie `access_token`.

Response:

```json
{
  "id": "uuid",
  "email": "usuario@email.com"
}
```

Erros:

- Sem token, token inválido ou token expirado deve retornar `401 Unauthorized`.

### `PATCH /users/me/password`

Altera a senha do usuário autenticado.

Request:

```json
{
  "current_password": "senha-atual",
  "new_password": "nova-senha-forte"
}
```

Response:

```json
{
  "password_updated": true
}
```

Autenticação:

- Usa cookie `access_token`.
- Usuário precisa estar autenticado.

Efeitos:

- Verifica se `current_password` corresponde à senha atual do usuário.
- Gera hash da `new_password`.
- Atualiza o hash da senha no usuário.
- Revoga refresh tokens ativos do usuário.
- Limpa cookies atuais ou força novo login.

Recomendação:

- Após alterar a senha, encerrar a sessão atual e pedir login novamente.
- Isso reduz risco caso algum refresh token antigo tenha vazado.

Validações:

- `current_password` obrigatória.
- `new_password` obrigatória.
- `new_password` deve respeitar regra mínima de senha.
- `new_password` não deve ser igual à senha atual.

Erros:

- Sem autenticação deve retornar `401 Unauthorized`.
- Senha atual incorreta deve retornar `401 Unauthorized` ou `400 Bad Request`, mas sem vazar detalhes sensíveis.
- Nova senha inválida deve retornar `422 Unprocessable Entity` ou erro equivalente de validação.

## Arquitetura esperada

O projeto usa uma organização inspirada em Clean Architecture:

```text
src/
  domain/
  application/
  infrastructure/
  presentation/
```

A regra principal é:

> Camadas internas não devem depender de camadas externas.

Ou seja:

- `domain` não importa FastAPI, banco, JWT, cookies ou bibliotecas externas de infraestrutura.
- `application` conhece casos de uso e contratos/interfaces.
- `infrastructure` implementa detalhes técnicos como banco, hash de senha, JWT e repositórios concretos.
- `presentation` contém FastAPI, rotas, schemas HTTP, cookies e dependências de autenticação.

## Organização sugerida de pastas

```text
src/
  domain/
    users/
      entities.py
      exceptions.py
      repositories.py
      value_objects.py
    auth/
      entities.py
      exceptions.py
      repositories.py

  application/
    auth/
      register_user.py
      login_user.py
      refresh_session.py
      logout_user.py
      get_current_user.py
      change_password.py
      dtos.py

  infrastructure/
    auth/
      jwt_token_service.py
      password_hasher.py
    persistence/
      user_repository.py
      refresh_token_repository.py

  presentation/
    http/
      routes/
        auth.py
        users.py
      dependencies/
        auth.py
      schemas/
        auth.py
        users.py
```

Essa estrutura pode ser ajustada caso o time decida usar banco específico ou ORM específico, mas a separação de responsabilidades deve ser mantida.

## Como pensar em cada camada

### `domain`

Contém o coração do negócio.

Exemplos:

- Entidade `User`.
- Entidade `RefreshToken`.
- Erros como `EmailAlreadyExists`, `InvalidCredentials`, `InvalidToken`.
- Contratos de repositório, por exemplo `UserRepository`.

O domínio não deve saber se a API usa FastAPI, PostgreSQL, SQLite, SQLAlchemy, JWT ou cookie.

Exemplo de responsabilidade correta:

- "Um usuário tem id, email e senha com hash."
- "Um refresh token pode estar ativo, expirado ou revogado."

Exemplo de responsabilidade errada no domínio:

- "Ler cookie da request."
- "Criar resposta HTTP."
- "Fazer query SQL diretamente."

### `application`

Contém os casos de uso.

Cada arquivo deve representar uma ação clara do sistema:

- `RegisterUserUseCase`
- `LoginUserUseCase`
- `RefreshSessionUseCase`
- `LogoutUserUseCase`
- `GetCurrentUserUseCase`
- `ChangePasswordUseCase`

O caso de uso coordena o fluxo:

1. Recebe dados de entrada.
2. Valida regras de aplicação.
3. Chama repositórios por interface.
4. Chama serviços por interface.
5. Retorna um DTO/resultado simples.

Importante:

- O caso de uso não deve receber `Request` ou `Response` do FastAPI.
- O caso de uso não deve setar cookie.
- O caso de uso não deve depender de SQLAlchemy diretamente.

### `infrastructure`

Contém detalhes técnicos.

Exemplos:

- Implementação concreta de hash de senha com `pwdlib`, `passlib` ou biblioteca equivalente.
- Implementação concreta de JWT.
- Implementação concreta dos repositórios usando banco.
- Configurações vindas de env.

Essa camada pode importar bibliotecas externas.

### `presentation`

Contém a API HTTP.

Exemplos:

- Rotas FastAPI.
- Schemas Pydantic de request/response.
- Leitura e escrita de cookies.
- Dependência `get_current_user`.
- Conversão de exceções de domínio/aplicação para HTTP status code.

Essa camada chama os casos de uso da aplicação.

## Princípios SOLID aplicados

### Single Responsibility Principle

Cada classe/função deve ter uma responsabilidade.

Exemplos:

- `PasswordHasher` só faz hash e verificação de senha.
- `JwtTokenService` só cria e valida JWT.
- `LoginUserUseCase` só executa o fluxo de login.
- Rota HTTP só traduz HTTP para caso de uso e caso de uso para HTTP.

### Open/Closed Principle

O sistema deve permitir trocar implementação sem alterar regra de negócio.

Exemplo:

- Hoje podemos usar SQLite.
- Amanhã podemos trocar para PostgreSQL.
- O caso de uso não deve mudar se os repositórios respeitarem a mesma interface.

### Liskov Substitution Principle

Qualquer implementação concreta de uma interface deve poder substituir outra sem quebrar o sistema.

Exemplo:

- `InMemoryUserRepository` nos testes.
- `SqlAlchemyUserRepository` em produção.
- Ambos devem cumprir o mesmo contrato.

### Interface Segregation Principle

Evitar interfaces grandes demais.

Exemplo:

- `UserRepository` cuida de usuário.
- `RefreshTokenRepository` cuida de refresh token.
- Não criar um `AuthRepository` gigante com tudo misturado.

### Dependency Inversion Principle

Casos de uso dependem de contratos, não de implementações concretas.

Exemplo:

- `LoginUserUseCase` depende de `UserRepository`, `PasswordHasher` e `TokenService`.
- Ele não depende diretamente de SQLAlchemy, bcrypt, JWT ou FastAPI.

## Modelos de domínio sugeridos

### `User`

Campos mínimos:

- `id`
- `email`
- `password_hash`
- `created_at`
- `updated_at`

Regras:

- Email deve ser único.
- Senha nunca deve ser salva pura.
- Email deve ser normalizado para comparação, preferencialmente lowercase.

### `RefreshToken`

Campos mínimos:

- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`

Regras:

- Token expirado não pode renovar sessão.
- Token revogado não pode renovar sessão.
- Logout deve revogar token.
- Refresh com rotação deve revogar token antigo.

## Variáveis de ambiente esperadas

Adicionar ao `.env.example`:

```env
JWT_SECRET_KEY=trocar-em-producao
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

Observação:

- Em produção, `COOKIE_SECURE` deve ser `true`.
- `JWT_SECRET_KEY` precisa ser forte e não pode ser commitada com valor real.

## Critérios de aceite

- Dado que não tenho conta, quando eu chamar `POST /auth/register` com email e senha válidos, então o sistema cria minha conta, retorna meus dados básicos e define cookies de sessão.
- Dado que já tenho conta, quando eu chamar `POST /auth/login` com credenciais corretas, então o sistema autentica e define cookies de sessão.
- Dado que informei senha errada, quando eu chamar `POST /auth/login`, então recebo `401 Unauthorized` com mensagem genérica.
- Dado que estou autenticado, quando eu chamar `GET /users/me`, então recebo meu `id` e `email`.
- Dado que não estou autenticado, quando eu chamar `GET /users/me`, então recebo `401 Unauthorized`.
- Dado que meu access token expirou mas meu refresh token ainda é válido, quando eu chamar `POST /auth/refresh`, então recebo novo access token em cookie.
- Dado que meu refresh token está expirado ou revogado, quando eu chamar `POST /auth/refresh`, então recebo `401 Unauthorized`.
- Dado que estou autenticado, quando eu chamar `POST /auth/logout`, então o refresh token atual é revogado e os cookies são limpos.
- Dado que fiz logout, quando eu tentar usar a sessão anterior, então o sistema não deve aceitar o refresh token antigo.
- Dado um email já cadastrado, quando eu tentar registrar novamente, então recebo erro adequado sem criar usuário duplicado.
- Dado que estou autenticado, quando eu chamar `PATCH /users/me/password` com senha atual correta e nova senha válida, então minha senha é alterada com hash seguro.
- Dado que estou autenticado, quando eu alterar minha senha, então meus refresh tokens anteriores são revogados e preciso autenticar novamente.
- Dado que estou autenticado, quando eu chamar `PATCH /users/me/password` com senha atual incorreta, então a senha não é alterada.
- Dado que não estou autenticado, quando eu chamar `PATCH /users/me/password`, então recebo `401 Unauthorized`.

## Testes esperados

Criar testes automatizados para:

- Cadastro com sucesso.
- Cadastro com email duplicado.
- Login com sucesso.
- Login com senha inválida.
- `GET /users/me` autenticado.
- `GET /users/me` sem autenticação.
- Refresh token válido.
- Refresh token expirado ou revogado.
- Logout revoga refresh token.
- Senha salva como hash, nunca como texto puro.
- Alteração de senha com sucesso.
- Alteração de senha com senha atual incorreta.
- Alteração de senha sem autenticação.
- Alteração de senha revoga refresh tokens ativos.

Os testes podem começar com repositórios em memória, desde que a arquitetura permita trocar depois por banco real.

## Tarefas técnicas sugeridas

- [ ] Criar entidades de domínio `User` e `RefreshToken`.
- [ ] Criar exceções de domínio/aplicação para email duplicado, credenciais inválidas e token inválido.
- [ ] Criar interfaces `UserRepository` e `RefreshTokenRepository`.
- [ ] Criar serviço/interface para hash de senha.
- [ ] Criar serviço/interface para geração e validação de tokens.
- [ ] Implementar `RegisterUserUseCase`.
- [ ] Implementar `LoginUserUseCase`.
- [ ] Implementar `RefreshSessionUseCase`.
- [ ] Implementar `LogoutUserUseCase`.
- [ ] Implementar `GetCurrentUserUseCase`.
- [ ] Implementar `ChangePasswordUseCase`.
- [ ] Criar schemas HTTP de auth e usuário.
- [ ] Criar rotas `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`.
- [ ] Criar rota `/users/me`.
- [ ] Criar rota `PATCH /users/me/password`.
- [ ] Criar dependência HTTP para obter usuário atual via cookie `access_token`.
- [ ] Configurar cookies HTTP-only.
- [ ] Adicionar variáveis no `.env.example`.
- [ ] Criar testes automatizados.
- [ ] Atualizar README com instruções básicas do módulo de auth.

## Observações de segurança

- Não retornar senha nem hash de senha em nenhuma resposta.
- Não logar tokens.
- Não logar senha.
- Não salvar refresh token puro no banco.
- Usar mensagem genérica para login inválido.
- Usar segredo JWT via variável de ambiente.
- Em produção, usar cookies com `Secure=true`.

## Definition of Done

- Endpoints implementados e documentados no OpenAPI do FastAPI.
- Testes automatizados passando.
- Cookies configurados corretamente.
- Refresh token persistente e revogável.
- Código separado por camadas, sem FastAPI dentro de `domain` ou `application`.
- README atualizado com exemplos rápidos de uso.
