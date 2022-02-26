##
## =============================================
## ============== Bases de Dados ===============
## ============== LEI  2020/2021 ===============
## =============================================
## =================== Not Demo ================
## =============================================
## =============================================
## === Department of Informatics Engineering ===
## =========== University of Coimbra ===========
## =============================================
##
## Authors: 
##   João Carlos Borges Silva nº2019216753
##   Sofia Santos Neves nº2019220082
##   Tatiana Silva Almeida nº2019219581
##   University of Coimbra

from flask import Flask, jsonify, request
import logging, psycopg2, time
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'Ok'



##
## Obtain user id with username <username>
##

def does_user_exist(username):    
    if(username == -1):
        return -1

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("begin transaction")
    cur.execute("""SELECT id_user 
                    FROM _user 
                    WHERE username = %s""", (username,))
    rows = cur.fetchall()
    cur.execute("commit")

    if(len(rows) == 0):
        return -1
    else:
        return rows[0][0]
    

##
##
## Add a new user in a JSON payload
## 
##   Registo de utilizadores. Criar um novo utilizador, inserindo os dados requeridos pelo modelo de dados.
##


@app.route("/dbproj/user", methods=['POST'])
def add_user():
    logger.info("###              DEMO: POST /user              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new user added  ----")
    logger.debug(f'payload: {payload}')

    cur.execute("begin transaction")
    cur.execute("""SELECT username, email 
                     FROM _user 
                    WHERE username = %s OR email = %s""", (payload["username"], payload["email"]))
    rows = cur.fetchall()

    if len(rows) != 0:
        conn.close()
        result = "Error: username or email already exists! :( "
        return jsonify(result)
    else: 
        statement = """INSERT INTO _user(was_banned, username, email, passwords, admins) 
                       VALUES (FALSE, %s , %s,  %s, FALSE) """             
        values = (payload["username"], payload["email"], payload["passwords"])

        try:   
            cur.execute(statement, values)
   
            cur.execute("""SELECT id_user
                            FROM _user 
                            WHERE username = %s""", (payload["username"],))
            rows = cur.fetchall()
            result = f'UserId: {rows[0][0]}'
            cur.execute("commit")
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            result = f'Error: {error}!'
            cur.execute("rollback")

        finally:
            if conn is not None:
                conn.close()

        return jsonify(result)
    

def encode(user):
    payload = {'iat': datetime.utcnow(), 'exp': datetime.utcnow() + timedelta(minutes = 30), 'username': user}

    return jwt.encode(payload, "secret", algorithm="HS256")
    
    
def decode(token):
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])['username']
        return decoded
    except:
        return -1

def was_banned(user_id):
    conn = db_connection()
    cur = conn.cursor()
    
    cur.execute("""SELECT was_banned 
                     FROM _user
                     WHERE id_user = %s""", (user_id,))
    rows = cur.fetchall()
    conn.close()

    if(rows[0][0] == True):
        return True
    else:
        return False
    
    

##
##
## Update user authentication_token and token expire date based on the a JSON payload
##
##   Autenticação de utilizadores. Login com username e password, recebendo um token de autenticação em
## caso de sucesso, token esse que deve ser incluído nas chamadas subsequentes.
##

@app.route("/dbproj/user", methods=['PUT'])
def authenticate_user():
    logger.info("###              DEMO: PUT /user              ###")
    payload = request.get_json()
    logger.info("---- New user authenticated ----")
    logger.debug(f'payload: {payload}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("begin transaction")
    cur.execute("""SELECT username, passwords, was_banned
                     FROM _user 
                    WHERE username = %s""", (payload["username"],))
    rows = cur.fetchall()
    cur.execute("commit")
    conn.close()

    if len(rows) == 0:
        return jsonify("Error: User does not exist! :( ")
    elif rows[0][2] == True:
        return jsonify("Error: You have been banned! ")

    row = rows[0]
    logger.debug("---- user authenticating  ----")
    logger.debug(row)
    content = {'username': row[0], 'passwords': row[1]}
    if (content["passwords"] == payload["passwords"]):
        try:
            result = f'AuthToken: {encode(payload["username"])}'
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            result = 'Error: Failed to authenticate user!'
        return jsonify(result)
    else:
        return jsonify("Error: Password does not match!")




## Get all currently active auctions based on the a JSON payload
##
##      Criar um novo leilão. Cria-se um leilão começando por identificar o artigo que se pretende comprar. Para
## simplificar, considera-se que cada artigo tem um código EAN/ISBN que o identifica univocamente. Cada
## leilão deve igualmente ter um título, uma descrição e quaisquer detalhes adicionais que considere
## necessários. Para criar o leilão, o vendedor indica o preço mínimo que está disposto a receber, bem como a
## data, hora e minuto em que o leilão termina.
##

@app.route("/dbproj/auction", methods=['POST'])
def add_auction():
    logger.info("###              DEMO: POST /auction              ###")
    payload = request.get_json()

    logger.info("---- new auction created ----")
    logger.debug(f'payload: {payload}')


    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("User does not have permissions to create auction since it was banned.")
        else:
            conn = db_connection()
            cur = conn.cursor()

            valid_item_conditions = ["NEW", "USED", "NOT SPECIFIED"]
            date = datetime.now()
            dateFinish = datetime.strptime(payload["final_date"],'%d/%m/%y %H:%M:%S')
            try:
                cur.execute("begin transaction")
                statement = """INSERT INTO auction(status, initial_price, min_price, title, description, condition, creation_date, last_update_date, final_date, actual_winner, _user_id_user) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """            
                values = ("ACTIVE", payload["initial_price"], payload["initial_price"], payload["title"], payload["description"], payload["condition"], date, date, dateFinish, user_id, user_id)
                
                if payload["condition"] not in valid_item_conditions:
                    result = "Error: Please, insert a valid type of condition [NEW, USED, NOT SPECIFIED]"
                    return jsonify(result)
                else:
                    if (dateFinish < date):
                        result = "Error: Please, insert a date after the current time"
                        return jsonify(result)
                    else:
                        try:
                            cur.execute(statement, values)
                            cur.execute("""SELECT ean
                                            FROM auction
                                            WHERE _user_id_user = %s and creation_date = %s""", (user_id, date))
                            rows = cur.fetchall()

                            result = f'EAN: {rows[0][0]}!'
                            cur.execute("commit")
                        except (Exception, psycopg2.DatabaseError) as error:
                            logger.error(error)
                            result = f'Error: Failed to create the auction!'
                            cur.execute("rollback")
                        finally:
                            if conn is not None:
                                conn.close()

                        return jsonify(result)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to create the auction!'
                cur.execute("rollback")
                conn.close()
                    
                return jsonify(result)




##
##
## Get all currently active auctions based on the a JSON payload
##
##      Listar todos os leilões existentes. Deve poder-se listar os leilões que estão a decorrer, obtendo uma lista
## de identificadores e descrições.
##

@app.route("/dbproj/auctions", methods=['GET'], strict_slashes=True)
def get_all_auctions():
    logger.info("###              DEMO: GET /dbproj/auctions              ###")

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("Error: You have been banned! ")

        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, description
                                FROM auction 
                                WHERE status = %s""", ('ACTIVE',))
                rows = cur.fetchall()

                payload = []
                logger.debug("---- users  ----")
                if(len(rows) == 0):
                    result = "Error: Currently there are no active auctions!"
                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)

                else:
                    for row in rows:
                        logger.debug(row)
                        
                        content = {'EAN': row[0], 'description': row[1]}
                        payload.append(content)  # appending to the payload to be returned
                    cur.execute("commit")
                    conn.close()
                    return jsonify(payload)

            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to list all auctions!'
                cur.execute("rollback")
                conn.close()
                return jsonify(result)


##
## Get all auctions by EAN or by keyword based on the a JSON payload
##
##  Pesquisar leilões existentes. Deve poder-se listar os leilões que estão a decorrer, pesquisando pelo código
## EAN/ISBN ou pela descrição do artigo. Esta listagem apresenta o identificador e descrição de cada leilão
## que obedeça ao critério da pesquisa.
##
 
@app.route("/dbproj/auctions/<keyword>", methods=['GET'])
def search_auction(keyword):
    logger.info("###              /dbproj/auctions/<keyword>             ###")
    logger.debug(f'keyword: {keyword}')  
    
    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("Error: You have been banned! ")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                space_before = "%" + keyword.upper()
                space_before_and_after = "% " + keyword.upper() + " %"
                space_after = keyword.upper() + "%"

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, description
                                FROM auction 
                                WHERE status = %s AND
                                    (CAST(ean AS VARCHAR) LIKE %s OR
                                    UPPER(description) LIKE %s
                                    OR UPPER(description) LIKE %s
                                    OR UPPER(description) LIKE %s) """, ("ACTIVE", keyword, space_before, space_before_and_after, space_after))
                rows = cur.fetchall()

                payload = []
                if(len(rows) == 0):
                    result = "Error: No action was found!"
                    
                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)
                    
                else:
                    for row in rows:
                        logger.debug(row)
                        content = {'EAN': row[0], 'description': row[1]}
                        payload.append(content)  # appending to the payload to be returned

                    cur.execute("commit")
                    conn.close()
                    return jsonify(payload)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to search the auction!'
                cur.execute("rollback")
                conn.close()
                return jsonify(result)




##
##
## Get an auction by EAN and all its mural messages and bids based on the a JSON payload
##
##      Consultar detalhes de um leilão. Para qualquer leilão escolhido, deve poder-se obter todos os detalhes
## relativos à descrição do artigo, ao término do leilão, às mensagens escritas no seu mural (ver abaixo) e ao
## histórico de licitações efetuadas nesse mesmo leilão.
##

@app.route("/dbproj/auction/<ean>", methods=['GET'])
def get_auction(ean):
    logger.info("###              DEMO: GET /dbproj/auction/<ean>            ###")
    logger.debug(f'auction: {ean}')  

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, title, min_price, status, description, condition, final_date 
                                FROM auction 
                                WHERE ean = %s""", (ean,))
                rows = cur.fetchall()

                if(len(rows) == 0):
                    result="Error: Auction not found :("

                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)
                    
                else:
                    result=[]
                    row = rows[0]

                    logger.debug("---- selected auction  ----")
                    logger.debug(row)

                    cur.execute("""SELECT username, messages, date_of_message
                                    FROM _user, mural_message
                                    WHERE id_user = _user_id_user
                                         AND auction_ean= %s""", (ean,))
                    
                    messages=cur.fetchall()

                    cur.execute("""SELECT username, bid_value, is_valid
                                    FROM _user, bid
                                    WHERE id_user = _user_id_user
                                        AND auction_ean= %s""", (ean,) )
                    
                    bids=cur.fetchall()

                    result.append('Details:')
                    result.append({'EAN': row[0], 'title': row[1], 'min_price': row[2], 'status': row[3], 'description': row[4], 'conditon': row[5], 'final_date': row[6]})
                    
                    result.append('Mural messages:')
                    for message in messages:
                        result.append({'Username': message[0], 'Message':message[1], 'Data':message[2]})

                    result.append('Bids:')
                    for bid in bids:
                        result.append({'Username':bid[0], 'Value':bid[1], 'Is valid?': bid[2]})

                    cur.execute("commit")
                    conn.close()
                    return jsonify(result)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to get the auction!'
                conn.close()
                return jsonify(result)




## Listar todos	os leilões em que o	utilizador tenha atividade.
##
##    Listar todos os leilões em que o utilizador tenha atividade. Um utilizador deve poder listar os leilões
## nos quais tem ou teve alguma atividade, seja como criador do leilão seja como licitador. Esta listagem
## sumaria os detalhes de cada leilão.  
##

@app.route("/dbproj/user/auctions_activity", methods=['GET'])
def user_auctions_activity():
    logger.info("###              DEMO: GET /dbproj/user/auctions_activity            ###")

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                cur.execute("""SELECT DISTINCT au.ean, au.description
                                FROM auction as au, bid as b
                                WHERE au._user_id_user = %s OR
                                        (b._user_id_user = %s and b.auction_ean=au.ean)""", (user_id,user_id))
                rows = cur.fetchall()
                
                if(len(rows) == 0):
                    cur.execute("rollback")
                    conn.close()
                    return jsonify("The user has no activity :/")
                    
                else:
                    payload = []
                    for row in rows:
                        logger.debug(row)
                        
                        content = {'EAN': row[0], 'description': row[1]}
                        payload.append(content)  # appending to the payload to be returned

                    cur.execute("commit")
                    conn.close()
                    return jsonify(payload)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to list all user activities!'

                cur.execute("rollback")
                conn.close()
                return jsonify(result)





## Get an auction bid by EAN based on the a JSON payload
##
##      Efetuar uma licitação num leilão. Um comprador pode licitar com um preço mais alto num determinado
## leilão, desde que o leilão não tenha terminado e que não haja uma sua licitação mais alta do que a que está
## a fazer e seja, pelo menos, superior ao preço mínimo.
##

@app.route("/dbproj/bid/<ean>/<bidding>", methods=['GET'])
def add_bidding(ean, bidding):
    logger.info("###              DEMO: GET /dbproj/bid/             ###")
    payload = request.get_json()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                logger.info("---- new bid done  ----")
                logger.debug(f'auction: {ean} and bidding: {bidding}')

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, min_price, _user_id_user
                                FROM auction 
                                WHERE ean = %s 
                                    AND status = 'ACTIVE'""", (ean, ))
                rows = cur.fetchall()
                

                if len(rows) == 0:
                    result = "Error: Auction does not exist or is not ACTIVE at the moment! :("
                    conn.close()
                    return jsonify(result)
                else: 
                    row = rows[0]
                    if(row[2]==user_id):
                        result = "Error: It is weird that you want to bid in your own auction! I can not allow that >:)"
                        conn.close()
                        return jsonify(result)

                    if(float(bidding) <= row[1]):
                        result = "Error: Your bidding must exceed the current auction listing price."
                        cur.execute("rollback")
                        conn.close()

                        return jsonify(result)
                    else:
                        statement = """INSERT INTO bid(bid_value, is_valid, _user_id_user, auction_ean) 
                                    VALUES ( %s, TRUE, %s, %s) """             
                        values = (bidding, user_id, ean)

                        try:
                            cur.execute(statement, values)
                            
                            # ======= NOTIFICATIONS ========= 
                            cur.execute("""SELECT actual_winner, _user_id_user
                                            FROM  auction
                                        WHERE ean = %s""", (ean, ))
                            rows2 = cur.fetchall()
                            
                            
                            date = datetime.now()
                            if(rows2[0][0]!=rows2[0][1]):
                                message = f"Your bid for auction {ean} is outdated."
                                cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, date, rows2[0][0]))

                            message = f"Your auction {ean} has a new bid."
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                VALUES ( %s, FALSE, %s, %s)""", (message, date, row[2]))           

                            # ======= UPDATE AUCTION =========                     
                            cur.execute("""UPDATE auction 
                                            SET min_price = %s, actual_winner = %s
                                            WHERE ean = %s""", (bidding, user_id, ean))
                            result = f'Bidding done!'
                            cur.execute("commit")

                        except (Exception, psycopg2.DatabaseError) as error:
                            logger.error(error)
                            result = f'Error: Failed to insert user {payload["username"]}!'
                            cur.execute("rollback")

                        finally:
                            if conn is not None:
                                conn.close()

                        return jsonify(result)
                        
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to add a bid!'
                conn.close()
                
                return jsonify(result)
  


##
##
## Edit auction textual properties
##
##    Editar propriedades de um leilão. O vendedor pode ajustar todas as descrições textuais relativas a um
## leilão seu, sendo que todas as versões anteriores devem ficar guardadas e poder ser consultadas
## posteriormente para referência.
##

@app.route("/dbproj/auction/<ean>", methods=['PUT'])
def edit_auction_properties(ean):
    logger.info("###              DEMO: PUT /dbproj/auction/<ean>            ###")
    payload = request.get_json()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else:  
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, title, description, status
                                FROM auction
                                WHERE ean = %s
                                    AND _user_id_user = %s""", (ean, user_id))
                rows = cur.fetchall()
                

                result = ""

                if(len(rows) == 0 or rows[0][3]!='ACTIVE'):
                    conn.close()
                    result = f"Error: Auction does not exist for user {user_id} or is not active! :("

                    conn.close()
                    return jsonify(result)
                    
                else:
                    row=rows[0]
                    time = datetime.now()

                    statement = """INSERT INTO auction_update(alteration_date, past_descriptions, past_title, auction_ean) 
                                    VALUES ( %s, %s, %s, %s) """             
                    values = (time, row[2], row[1], row[0])
                        
                    if(len(payload) == 2):
                        try:
                            cur.execute(statement, values)

                            cur.execute("""UPDATE auction 
                                            SET title = %s, description = %s, last_update_date = %s
                                            WHERE ean = %s""", (payload["title"], payload["description"], time, ean))

                            cur.execute("""SELECT ean, title, min_price, status, description, condition, final_date 
                                            FROM auction 
                                            WHERE ean = %s""", (ean,))
                            rows = cur.fetchall()
                            row = rows[0]
                            result = {'EAN': row[0], 'title': row[1], 'min_price': row[2], 'status': row[3], 'description': row[4], 'conditon': row[5], 'final_date': row[6]}
                            cur.execute("commit")

                        except (Exception, psycopg2.DatabaseError) as error:
                            logger.error(error)
                            cur.execute("rollback")
                            return jsonify(f'Error: Failed to update auction {ean} textual descriptions!')

                        finally:
                            if conn is not None:
                                conn.close()
                        return jsonify(result)

                    elif(len(payload) == 1):
                        if('title' in payload):
                            try:
                                cur.execute(statement, values)

                                cur.execute("""UPDATE auction 
                                                SET title = %s, last_update_date = %s
                                                WHERE ean = %s""", (payload["title"], time, ean))
                                
                                cur.execute("""SELECT ean, title, min_price, status, description, condition, final_date 
                                                FROM auction 
                                                WHERE ean = %s""", (ean,))
                                rows = cur.fetchall()
                                row = rows[0]
                                result = {'EAN': row[0], 'title': row[1], 'min_price': row[2], 'status': row[3], 'description': row[4], 'conditon': row[5], 'final_date': row[6]}
                                
                                cur.execute("commit")

                            except (Exception, psycopg2.DatabaseError) as error:
                                logger.error(error)
                                result = f'Error: Failed to update auction title!'

                                cur.execute("rollback")
                  

                            finally:
                                if conn is not None:
                                    conn.close()

                            return jsonify(result)
                            
                        elif('description' in payload):
                            try:
                                cur.execute(statement, values)

                                cur.execute("""UPDATE auction 
                                                SET description = %s, last_update_date = %s
                                                WHERE ean = %s""", (payload["description"], time, ean))

                                cur.execute("""SELECT ean, title, min_price, status, description, condition, final_date 
                                                FROM auction 
                                                WHERE ean = %s""", (ean,))
                                rows = cur.fetchall()
                                row = rows[0]
                                result = {'EAN': row[0], 'title': row[1], 'min_price': row[2], 'status': row[3], 'description': row[4], 'conditon': row[5], 'final_date': row[6]}

                                cur.execute("commit")

                            except (Exception, psycopg2.DatabaseError) as error:
                                logger.error(error)
                                result = f'Error: Failed to update auction description!'

                                cur.execute("rollback")

                            finally:
                                if conn is not None:
                                    conn.close()
                            return jsonify(result)
                            

                    else:
                        cur.execute("rollback")
                        conn.close()

                        return jsonify("Error: invalid number of arguments.")
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to edit auction properties!'

                conn.close()
                return jsonify(result)

## Create a new message in mural for auction
##
##  Escrever mensagem no mural de um leilão. Cada leilão deve ter um “mural” onde poderão ser escritos
## comentários, questões e esclarecimentos relativos ao leilão.
##

@app.route("/dbproj/<ean>/mural_message", methods=['POST'])
def mural_message_auction(ean):
    logger.info("###              DEMO: POST /dbproj/<ean>/mural_message            ###")
    payload = request.get_json()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    if user_id == -1 or verify == -1:
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    else: 
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                cur.execute("""SELECT ean, title, description, _user_id_user
                                FROM auction
                                WHERE ean = %s""", (ean,))
                rows = cur.fetchall()
                

                if(len(rows) == 0):
                    result = f"Error: Auction does not exist! :("
                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)
                    
                else: 
                    creator=rows[0][3]
                    time = datetime.now()
                    statement = """INSERT INTO mural_message(messages, date_of_message, _user_id_user, auction_ean) 
                                    VALUES ( %s, %s, %s, %s) """             
                    values = (payload["message"], time, user_id, ean)


                    try:
                        cur.execute(statement, values)

                        result = f'Message has been written!'

                        # ======= NOTIFICATIONS ========= 
                        cur.execute("""SELECT DISTINCT _user_id_user
                                        FROM  bid
                                    WHERE  auction_ean = %s
                                            AND _user_id_user <> %s
                                            AND is_valid=True""", (ean, user_id))
                        rows = cur.fetchall()
                        
                        if(len(rows) != 0):
                            message = f"New message in Mural Message for auction {ean}"
                            for row in rows:
                                cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, time, row[0]))      
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, time, creator))
                        cur.execute("commit")

                    except (Exception, psycopg2.DatabaseError) as error:
                        logger.error(error)
                        result = f'Error: Failed to write this message!'

                        cur.execute("rollback")

                    finally:
                        if conn is not None:
                            conn.close()

                    return jsonify(result)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to list mural messages!'

                cur.execute("rollback")
                conn.close()
                return jsonify(result)

##
##      An administrator can cancel the auction
##
##      Entrega imediata de notificações a utilizadores. Os utilizadores recebem imediatamente na sua caixa de
## entrada as notificações acerca das mensagens publicadas, e deverão estar disponíveis no endpoint
## correspondente. O criador de um leilão é notificado de todas as mensagens relativas a esse leilão. Todos os
## utilizadores que tiverem escrito num mural passam a ser notificados acerca de mensagens escritas nesse
## mesmo mural.
##

@app.route("/dbproj/notification_box/<view>", methods=['GET'])
def check_notification_box(view):
    logger.info("###              DEMO: GET /dbproj/notification_box/<view>            ###")

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    types = ["all", "not_read"]

    if user_id == -1 or verify == -1:
        return jsonify("Error: User is not authenticated! :( ")
    elif  view not in types:
        return jsonify("Error: in /dbproj/notification_box/<view>, view must be 'all' or 'not_read'.")
    else:
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                conn = db_connection()
                cur = conn.cursor()

                cur.execute("begin transaction")
                if(view == "all"):
                    cur.execute("""SELECT id_notification, creation_date, messages, was_read
                                    FROM notification
                                    WHERE _user_id_user = %s""", (user_id, ))
                else:
                    cur.execute("""SELECT id_notification, creation_date, messages, was_read
                                    FROM notification
                                    WHERE _user_id_user = %s
                                        AND was_read = FALSE""", (user_id, ))
                rows = cur.fetchall()
                
                
                if(len(rows) == 0):
                    result = f"You do not have any notifications to read :("
                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)
                    
                else:
                    result = []
                    try:
                        for row in rows:                    
                            result.append({"ID_notification": row[0], "Date": row[1], "Message":row[2]})
                            cur.execute("""UPDATE notification
                                            SET was_read = TRUE
                                            WHERE was_read = FALSE 
                                                AND id_notification = %s""", (row[0],))
                            cur.execute("commit")

                    except (Exception, psycopg2.DatabaseError) as error:
                        logger.error(error)
                        result = f'Error: Failed to write message!'
                        cur.execute("rollback")
                

                    finally:
                        if conn is not None:
                            conn.close()

                    return jsonify(result)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to check notification box!'
                cur.execute("rollback")
                conn.close()
                return jsonify(result)




@app.route("/dbproj/give_permissions", methods=['PUT'])
def give_permissions():
    logger.info("###              DEMO: PUT /dbproj/give_permissions/          ###")
    payload = request.get_json()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("begin transaction")
    cur.execute("""SELECT admins 
                     FROM _user
                    WHERE id_user = %s""", (user_id,))
    
    rows = cur.fetchall()

    if user_id == -1 or verify == -1:
        return jsonify("Error: User is not authenticated! :( ")
    
    elif(rows[0][0] != True):
        return jsonify("Error: You do not have admin permissions.")

    else: 
        if(was_banned(user_id)):
            return jsonify("You have been banned!")
        else:
            try:
                cur.execute("""SELECT admins
                                FROM _user
                                WHERE username = %s""", (payload["username"], ))
                rows = cur.fetchall()
                if(len(rows) == 0):
                    cur.execute("rollback")
                    conn.close()
                    return jsonify("Error: The user does not exist :(")
                elif (rows[0][0] == True ):
                    cur.execute("rollback")
                    conn.close()
                    return jsonify("Error: The user is already an admin.")
                else:
                    try:
                        cur.execute("""UPDATE _user
                                        SET admins = %s
                                        WHERE username = %s""", (True, payload["username"]))
                        cur.execute("commit")

                    except (Exception, psycopg2.DatabaseError) as error:
                        logger.error(error)
                        cur.execute("rollback")
                        conn.close()
                
                        return jsonify(f'Error: Failed to write message!')

                    finally:
                        if conn is not None:
                            conn.close()

                    return jsonify(f"User {payload['username']} was promoted to admin with success!")
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to give permissions!'
                cur.execute("rollback")
                conn.close()
                return jsonify(result)



         
##
##      Um administrador pode cancelar um leilão. Um administrador deve poder cancelar um leilão se tal for necessário. 
## O leilão continua a poder ser consultado pelos utilizadores, mas está dado como encerrado e não podem ser feitas licitações.
## Todos os utilizadores interessados recebem uma notificação. 
##

@app.route("/dbproj/auction_cancellation", methods=['PUT'])
def auction_cancellation():
    logger.info("###              DEMO: PUT /dbproj/auction_cancellation            ###")
    payload = request.get_json()
    date = datetime.now()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("begin transaction")
    cur.execute("""SELECT admins 
                     FROM _user
                    WHERE id_user = %s""", (user_id,))
    rows = cur.fetchall()

    if user_id == -1 or verify == -1:
        cur.execute("rollback")
        conn.close()
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    elif(rows[0][0] != True):
        cur.execute("rollback")
        conn.close()
        return jsonify("Error: You do not have admin permissions.")
    else: 
        if(was_banned(user_id)):
            cur.execute("rollback")
            conn.close()
            return jsonify("User does not have permissions to create auction since it was banned.")
        else:
            try:
                cur.execute("""SELECT _user_id_user
                                FROM auction
                                WHERE ean = %s
                                      AND status = 'ACTIVE' """, (payload["ean"], ))
                rows = cur.fetchall()
                if(len(rows)==0):
                    result = f"Error: Auction does not exist or is not currently active! :("
                    cur.execute("rollback")
                    conn.close()
                    return jsonify(result)
                else:
                    cur.execute("""UPDATE auction
                                    SET status = 'CANCELLED'
                                    WHERE ean = %s""", (payload["ean"],))
                    result = f"Auction {payload['ean']} was cencelled with success!"
                
                    # ======= NOTIFICATIONS ========= 
                    message=f"Your auction {payload['ean']} was cancelled"
                    cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                VALUES ( %s, FALSE, %s, %s)""", (message, date, rows[0][0]))

                    cur.execute("""SELECT DISTINCT _user_id_user
                                    FROM  bid
                                    WHERE  auction_ean = %s
                                            AND is_valid = True
                                            AND _user_id_user <> %s""", (payload["ean"], user_id))
                    rows = cur.fetchall()
                    
                    if(len(rows) != 0):
                        message = f"Auction {payload['ean']} was cancelled!"
                        for row in rows:
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                VALUES ( %s, FALSE, %s, %s)""", (message, date, row[0]))      
                    cur.execute("commit")
                
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to cancel this auction!'

            finally:
                if conn is not None:
                    conn.close()

            return jsonify(result)



##
##      Término do leilão na data, hora e minuto marcados
##
##      Término do leilão na data, hora e minuto marcados. No momento indicado pelo vendedor (data, hora e
## minuto) o leilão termina. Determina-se aí o vencedor e fecha-se a possibilidade de realizar mais licitações.
## Os detalhes desse leilão são atualizados e podem ser consultados posteriormente.
##

@app.route("/dbproj/<ean>/terminate_auction", methods=['PUT'])
def terminate_auction(ean):
    logger.info("###              DEMO: PUT /dbproj/<ean>/terminate_auction            ###")

    conn = db_connection()
    cur = conn.cursor()
    
    cur.execute("begin transaction")
    cur.execute("""SELECT ean, status, actual_winner, _user_id_user, final_date
                     FROM auction
                    WHERE ean = %s
                      AND status = 'ACTIVE' """, (ean,))
    rows = cur.fetchall()

    
    if(len(rows) == 0):
        result = f"Error: Auction does not exist or is not currently active! :("
        cur.execute("rollback")
        conn.close()
        return jsonify(result)

        
    else: 
        date = datetime.now()
        
        if(date > rows[0][4]):
            try:
                cur.execute("begin transaction")
                cur.execute("""UPDATE auction
                                SET status = 'TERMINATED'
                                where ean = %s""", (ean,))

                if(rows[0][2] != rows[0][3]):
                    message = f"You won the auction {ean}!!! :D"
                    cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                            VALUES ( %s, FALSE, %s, %s)""", (message, date, rows[0][2]))

                message = f"Your auction {ean} has terminated."
                cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                        VALUES ( %s, FALSE, %s, %s)""", (message, date, rows[0][3]))

                result = f"Auction {ean} has finished"
                cur.execute("commit")
                conn.close()
                return jsonify(result)

            except (Exception, psycopg2.DatabaseError) as error:
                logger.error(error)
                result = f'Error: Failed to terminate auction!'
            
            finally:
                if conn is not None:
                    conn.close()
            
            return jsonify(result)
        else:
            cur.execute("rollback")
            conn.close()
            return jsonify("Auction still has some time left to finish!")


        
##      Um administrador pode banir permanentemente um utilizador. Um
## administrador deve poder banir um utilizador se tal for necessário. Todos os leilões criados por esse
## utilizador são cancelados. Todas as licitações efetuadas por esse utilizador devem ser invalidadas (ainda
## que mantidas nos registos). Note que, ao invalidar uma licitação num leilão, quaisquer licitações superiores
## a essa devem ser igualmente invalidadas exceto a melhor delas, cujo valor se torna igual ao valor da que for
## invalidada. Automaticamente é criada uma mensagem no mural dos leilões afetados lamentando o
## incómodo e todos os utilizadores envolvidos devem receber uma notificação.
## 

@app.route("/dbproj/ban_user", methods=['PUT'])
def ban_user():
    logger.info("###              DEMO: PUT /dbproj/ban_user            ###")
    payload = request.get_json()

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    date = datetime.now()

    conn = db_connection()
    cur = conn.cursor()
    
    cur.execute("begin transaction")
    cur.execute("""SELECT admins 
                     FROM _user
                    WHERE id_user = %s""", (user_id,))
    rows = cur.fetchall()

    if user_id == -1 or verify == -1:
        cur.execute("rollback")
        conn.close()
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    elif(rows[0][0] != True):
        cur.execute("rollback")
        conn.close()
        return jsonify("Error: You do not have admin permissions.")
    else: 
        cur.execute("""SELECT id_user
                                FROM _user
                                WHERE username = %s""", (payload["username"],))
        aux = cur.fetchall()
        

        if(len(aux) == 0):
                    cur.execute("rollback")
                    conn.close()
                    return jsonify("Error: The user does not exist :(")
        else:
            user_id = aux[0][0] 
            if(was_banned(user_id)):
                cur.execute("rollback")
                conn.close()
                return jsonify("User was already banned.")
            else:
                try:
                    # ======== UPDATE USER STATUS FOR BANNED =========
                    cur.execute(""" UPDATE _user
                                    SET was_banned = True
                                    WHERE id_user = %s """, (user_id, ))
                    cur.execute("commit")

                    # ======== UPDATE USER AUCTIONS FOR CANCELLED =========
                    cur.execute("""SELECT ean
                                    FROM auction
                                    WHERE _user_id_user = %s""", (user_id, ))
                    rows_auctions = cur.fetchall()

                    for row in rows_auctions:
                        cur.execute("""UPDATE auction
                                        SET status = 'CANCELLED'
                                        WHERE ean = %s""", (row[0],))
                    
                        cur.execute("""SELECT DISTINCT _user_id_user
                                        FROM bid
                                        WHERE auction_ean = %s
                                            AND is_valid = True """, (row[0],))
                        biders = cur.fetchall()

                        message=f"Auction {row[0]} was cancelled because the creator was banned.Sorry for the trouble!!"
                        for user in biders:
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, date, user))

                    # ======== SEARCH ALL USER BIDS ===========
                    cur.execute("""SELECT id_bid, auction_ean, bid_value
                                    FROM bid
                                    WHERE _user_id_user = %s""", (user_id, ))
                    rows = cur.fetchall()

                    for row in rows:
                        # ======== UPDATE USER BIDS FOR INVALID ===========
                        cur.execute("""UPDATE bid
                                        SET is_valid = FALSE
                                        WHERE id_bid = %s """, (row[0], ))

                    cur.execute("""SELECT DISTINCT auction_ean
                                    FROM bid
                                    WHERE _user_id_user = %s""", (user_id, ))
                    rows = cur.fetchall()

                    for ean in rows:
                        # ======== SEARCH FOR BANNED USER MIN BID VALUE  ===========
                        cur.execute("""SELECT bid_value
                                            FROM bid
                                            WHERE _user_id_user = %s
                                                AND auction_ean = %s
                                            ORDER BY bid_value asc""", (user_id, ean[0]))
                        min_value_bid = cur.fetchall()

                        cur.execute("""SELECT id_bid
                                        FROM bid
                                        WHERE auction_ean = %s
                                                AND bid_value > %s 
                                                AND is_valid = True
                                        ORDER BY id_bid asc""", (ean[0], min_value_bid[0][0]))
                        higher_bids = cur.fetchall()

                        if(len(higher_bids) == 0): ## NAO EXISTEM BIDS MAIORES QUE A MAIS PEQUENA DO GAJO BANIDO
                            cur.execute("""SELECT id_bid
                                            FROM bid
                                            WHERE auction_ean = %s
                                                AND bid_value < %s 
                                                AND is_valid = True
                                            ORDER BY id_bid desc""", (ean[0], min_value_bid[0][0]))
                            lower_bids = cur.fetchall()

                            if(len(lower_bids)== 0):    ## SÓ EXISTIA MESMO AQUELA LICITACAO E O WINNER VAI PASSAR A SER O OWNER
                                cur.execute("""SELECT _user_id_user
                                                FROM auction
                                            WHERE ean = %s""", (ean[0],))
                                owner = cur.fetchall()

                                cur.execute("""UPDATE auction
                                                SET actual_winner = %s, 
                                                    min_price = (SELECT initial_price
                                                                FROM auction
                                                                WHERE ean = %s)
                                                WHERE ean = %s""", (owner[0][0], ean[0], ean[0]))

                            else:  
                                ## METER O WINNER COMO O PRIMEIRO ANTES DO BANIDO
                                cur.execute("""UPDATE auction
                                                SET actual_winner = (SELECT _user_id_user
                                                                FROM bid
                                                                WHERE id_bid = %s), 
                                                    min_price = (SELECT bid_value
                                                                FROM bid
                                                                WHERE id_bid = %s)
                                                WHERE ean = %s""", (lower_bids[0][0], lower_bids[0][0], ean[0]))

                        else: 
                            for bids in higher_bids:
                                if(bids[0]!=higher_bids[0][0]):
                                    print("entrou no if")
                                    cur.execute(""" UPDATE bid
                                                        SET is_valid = False
                                                        WHERE id_bid = %s """, (bids[0], ))                       

                            cur.execute("""UPDATE auction
                                            SET actual_winner = (SELECT _user_id_user
                                                                FROM bid
                                                                WHERE id_bid = %s), 
                                                min_price = %s
                                                WHERE ean = %s""", (higher_bids[0][0],min_value_bid[0][0], ean[0]))

                            cur.execute("""UPDATE bid
                                            SET bid_value = %s
                                                WHERE id_bid = %s""", (min_value_bid[0][0], higher_bids[0][0]))
                                            
                        cur.execute("""SELECT DISTINCT _user_id_user
                                        FROM bid
                                        WHERE auction_ean = %s
                                            AND is_valid = True""", (ean[0], ))
                        bid_users = cur.fetchall()
                        message = f"A liciting user from {ean[0]} auction was banned. Sorry for the trouble!!"
                        for user in bid_users:
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, date, user))

                        cur.execute("""SELECT DISTINCT _user_id_user
                                        FROM auction
                                        WHERE ean = %s""", (ean[0], ))
                        bid_users = cur.fetchall()
                        message = f"A liciting user from your auction {ean[0]} was banned. Sorry for the trouble!!"
                        for user in bid_users:
                            cur.execute("""INSERT INTO notification(messages, was_read, creation_date, _user_id_user) 
                                                    VALUES ( %s, FALSE, %s, %s)""", (message, date, user))

                    
                    result = f"User {payload['username']} was successfully banned!"
                    cur.execute("commit")
                except (Exception, psycopg2.DatabaseError) as error:
                        logger.error(error)
                        result = f'Error: Failed to ban user!'
                        cur.execute("rollback")
                    
                finally:
                    if conn is not None:
                        conn.close()
                
                
                return jsonify(result)


##      Um administrador pode obter estatísticas de atividade na aplicação. Um
## administrador deve poder consultar estatísticas da utilização da aplicação: top 10 utilizadores com mais
## leilões criados, top 10 utilizadores que mais leilões venceram, número total de leilões nos últimos 10 dias.
##

@app.route("/dbproj/app_stats", methods=['GET'])
def app_stats():
    logger.info("###              DEMO: GET /dbproj/app_stats            ###")

    verify = decode(request.args['token'])
    user_id = does_user_exist(verify)

    date = datetime.now()

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("begin transaction")
    cur.execute("""SELECT admins 
                     FROM _user
                    WHERE id_user = %s""", (user_id,))
    rows = cur.fetchall()

    result=""

    if user_id == -1 or verify == -1:
        cur.execute("rollback")
        conn.close()
        result = "Error: User is not authenticated! :( "
        return jsonify(result)
    elif(rows[0][0] != True):
        cur.execute("rollback")
        conn.close()
        return jsonify("Error: You do not have admin permissions.")
    else: 
        if(was_banned(user_id)):
            cur.execute("rollback")
            conn.close()
            return jsonify("User was already banned.")
        else:
            try:
                cur.execute("""select username, count(_user_id_user) 
                                from _user, auction
                                where id_user=_user_id_user
                                group by username
                                ORDER by count(_user_id_user) desc""")
                top10moreauctions = cur.fetchall()
                
                cur.execute("""SELECT username, count(_user_id_user) 
                                FROM _user, auction
                                WHERE id_user=actual_winner AND
                                        status='TERMINATED' AND
                                        actual_winner<>_user_id_user
                                GROUP by username
                                ORDER by count(_user_id_user) desc""")
                
                top10morewins = cur.fetchall()

                cur.execute("""SELECT ean
                                FROM auction
                                WHERE creation_date >=current_date - interval '10' day """)

                auctionslast10days = cur.fetchall()

                result += """Top 10 users with the most created auctions\n"""

                count = 0
                for user in top10moreauctions:
                    if(count == 10):
                        break
                    result += "- " + str(user[0]) + " with "+str(user[1])+" auctions created\n"
                    count += 1
                
                count = 0
                result += """\nTop 10 users that won the most auctions\n"""
                for user in top10morewins:
                    if(count == 10):
                        break
                    result += "- " + str(user[0]) + " won "+str(user[1])+" auctions\n"
                    count += 1
 
                result += """\nTotal number of auctions in the last 10 days: """+str(len(auctionslast10days))
                cur.execute("commit")
                conn.close()

            except (Exception, psycopg2.DatabaseError) as error:
                result = f"Error: It was not possible to print statistics."
                cur.execute("rollback")
                conn.close()

        return result


    

##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(user="postgres",
                          password="postgres",
                          host="localhost",
                          port="5432",
                          database="projBD")
    return db


##########################################################
## MAIN
##########################################################
if __name__ == "__main__":
    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                                  '%H:%M:%S')
    # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    time.sleep(1)  # just to let the DB start before this print :-)

    logger.info("\n---------------------------------------------------------------\n" +
                "API v1.0 online: http://localhost:8080/dbproj/\n\n")

    app.run(host="localhost", port="8080", debug=True, threaded=True)