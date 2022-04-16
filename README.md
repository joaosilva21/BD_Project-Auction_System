# BD_Project-Auction_System

- [x] Finished

## Index
- [Description](#description)
- [Technologies used](#technologies-used)
- [To run this project](#to-run-this-project)
- [Notes important to read](#notes-important-to-read)
- [Authors](#authors)

## Description
This project was developed for Databases subject @University of Coimbra, Informatics Engineering <br>
Consists in develop a program that implements an Auction System using the framework Psycopg2 and other database elements

#### Main Languages:
![](https://img.shields.io/badge/Python-333333?style=flat&logo=python&logoColor=4F74DA) ![](https://img.shields.io/badge/PostgresSQL-333333?style=flat&logo=postgresql&logoColor=white)

## Technologies used:
1. Python
    - [Version 3.9](https://www.python.org/downloads/release/python-390/)
2. [Postman](https://www.postman.com/downloads/)
3. [PgAdmin](https://www.pgadmin.org/download/)
4. Libraries
    - [Flask](https://pypi.org/project/Flask/)
    - [Psycopg2](https://pypi.org/project/psycopg2/)

## To run this project:
After installing PgAdmin, Postman and all libraries:
1. Create a database with name "projBD"<br>
![image](https://i.imgur.com/mK3L3kK.png)
![image](https://i.imgur.com/bTTcomU.png)
2. Download the src folder and create the tables using the script "Tabelas.sql"<br>
![image](https://i.imgur.com/h0LF7Iw.png)
3. Before pass to Postman create an Admin User<br>
![image](https://i.imgur.com/jrRD7O3.png)
4. In Postman create some end-points (for more information see the Report)<br>
![image](https://i.imgur.com/dBgYSH3.png)
5. Create a folder called "logs" on same folder of the file "Auction.py" with a file called "log_file.log".
6. Finally just run it
```shellscript
[your-disk]:[name-path]> python Auctions.py
```

## Notes important to read:
   - The file "log_file.log" contains some information about the execution of the program (the same information will be printed on the shell)
   - To know how to use all the end-points see the Report, they are all described there
   - Some end-points need a token of authentication<br>
   ![image](https://i.imgur.com/6GJpM8z.png)

## Authors:
- [João Silva](https://github.com/ikikara)
- [Sofia Neves](https://github.com/sneves-git)
- [Tatiana Almeida](https://github.com/TatianaSAlmeida)
