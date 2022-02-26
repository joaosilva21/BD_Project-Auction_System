CREATE TABLE auction (
    ean         serial,
    status         VARCHAR(20) NOT NULL,
    initial_price     FLOAT(8) NOT NULL,
    min_price     FLOAT(8) NOT NULL,
    title         VARCHAR(250) NOT NULL,
    description     VARCHAR(1000) NOT NULL,
    condition     VARCHAR(50) NOT NULL,
    creation_date     TIMESTAMP NOT NULL,
    last_update_date TIMESTAMP NOT NULL,
    final_date     TIMESTAMP NOT NULL,
    actual_winner     BIGINT NOT NULL,
    _user_id_user     BIGINT NOT NULL,
    PRIMARY KEY(ean)
);

CREATE TABLE _user (
	was_banned		 BOOL NOT NULL,
	id_user		 SERIAL,
	username		 VARCHAR(50) UNIQUE NOT NULL,
	email		 VARCHAR(100) UNIQUE NOT NULL,
	passwords		 VARCHAR(50) NOT NULL,
	admins		 BOOL NOT NULL,
	PRIMARY KEY(id_user)
);

CREATE TABLE mural_message (
	id_message	 SERIAL,
	messages	 VARCHAR(1000) NOT NULL,
	date_of_message TIMESTAMP NOT NULL,
	_user_id_user	 BIGINT,
	auction_ean	 BIGINT,
	PRIMARY KEY(id_message,_user_id_user,auction_ean)
);

CREATE TABLE bid (
	id_bid	 SERIAL,
	is_valid BOOL NOT NULL,
	bid_value	 FLOAT(20) NOT NULL,
	_user_id_user BIGINT,
	auction_ean	 BIGINT,
	PRIMARY KEY(id_bid,_user_id_user,auction_ean)
);

CREATE TABLE auction_update (
	alteration_date	 TIMESTAMP NOT NULL,
	past_descriptions VARCHAR(1000) NOT NULL,
	past_title	 VARCHAR(250) NOT NULL,
	auction_ean	 BIGINT,
	id_auction_update SERIAL,
	PRIMARY KEY(auction_ean, id_auction_update)
);

CREATE TABLE notification (
	id_notification SERIAL,
	messages	 VARCHAR(1000) NOT NULL,
	was_read	 BOOL NOT NULL,
	creation_date	 TIMESTAMP NOT NULL,
	_user_id_user	 BIGINT,
	PRIMARY KEY(id_notification,_user_id_user)
);

ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (_user_id_user) REFERENCES _user(id_user);
ALTER TABLE mural_message ADD CONSTRAINT mural_message_fk1 FOREIGN KEY (_user_id_user) REFERENCES _user(id_user);
ALTER TABLE mural_message ADD CONSTRAINT mural_message_fk2 FOREIGN KEY (auction_ean) REFERENCES auction(ean);
ALTER TABLE bid ADD CONSTRAINT bid_fk1 FOREIGN KEY (_user_id_user) REFERENCES _user(id_user);
ALTER TABLE bid ADD CONSTRAINT bid_fk2 FOREIGN KEY (auction_ean) REFERENCES auction(ean);
ALTER TABLE auction_update ADD CONSTRAINT auction_update_fk1 FOREIGN KEY (auction_ean) REFERENCES auction(ean);
ALTER TABLE notification ADD CONSTRAINT notification_fk1 FOREIGN KEY (_user_id_user) REFERENCES _user(id_user);
