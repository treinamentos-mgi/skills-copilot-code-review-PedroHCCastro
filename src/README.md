# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/auth/login?username={username}&password={password}`             | Autentica um professor e retorna um `token` de sessão (válido por 8 horas) |
| POST   | `/auth/logout`                                                    | Revoga o token de sessão (requer `Authorization: Bearer <token>`)    |
| GET    | `/announcements?active_only=true`                                 | Lista os anúncios (público). `active_only` retorna apenas os ativos   |
| POST   | `/announcements`                                                  | Cria um anúncio (requer `Authorization: Bearer <token>`). Corpo: `message`, `expires_at` (obrigatório), `start_date` (opcional) |
| PUT    | `/announcements/{announcement_id}`                                | Atualiza um anúncio (requer `Authorization: Bearer <token>`)         |
| DELETE | `/announcements/{announcement_id}`                                | Exclui um anúncio (requer `Authorization: Bearer <token>`)           |

Cada anúncio possui `status`: `active` (vigente), `scheduled` (ainda não começou) ou `expired` (expirado). A data de expiração não pode ser anterior à data de início.

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Todos os dados são armazenados em memória, o que significa que serão resetados quando o servidor for reiniciado.
