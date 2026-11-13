PRAGMA foreign_keys=ON;
CREATE TABLE app_user(user_id INTEGER PRIMARY KEY,created_at INTEGER NOT NULL);
CREATE TABLE seller(seller_id INTEGER PRIMARY KEY,seller_name TEXT NOT NULL);
CREATE TABLE category(category_id INTEGER PRIMARY KEY,category_name TEXT NOT NULL UNIQUE);
CREATE TABLE product(product_id INTEGER PRIMARY KEY,category_id INTEGER NOT NULL REFERENCES category,product_name TEXT NOT NULL);
CREATE TABLE offer(offer_id INTEGER PRIMARY KEY,seller_id INTEGER NOT NULL REFERENCES seller,product_id INTEGER NOT NULL REFERENCES product,current_price INTEGER NOT NULL CHECK(current_price>=0),is_active INTEGER NOT NULL CHECK(is_active IN(0,1)),UNIQUE(seller_id,product_id));
CREATE TABLE cart(cart_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES app_user,created_at INTEGER NOT NULL);
CREATE TABLE cart_item(cart_id INTEGER NOT NULL REFERENCES cart,offer_id INTEGER NOT NULL REFERENCES offer,quantity INTEGER NOT NULL CHECK(quantity>0),PRIMARY KEY(cart_id,offer_id));
CREATE TABLE user_session(session_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES app_user,started_at INTEGER NOT NULL);
CREATE TABLE customer_order(order_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES app_user,session_id INTEGER REFERENCES user_session,ordered_at INTEGER NOT NULL,status TEXT NOT NULL CHECK(status IN('confirmed','cancelled')));
CREATE TABLE order_item(order_id INTEGER NOT NULL REFERENCES customer_order,line_no INTEGER NOT NULL CHECK(line_no>0),offer_id INTEGER NOT NULL REFERENCES offer,quantity INTEGER NOT NULL CHECK(quantity>0),unit_price INTEGER NOT NULL CHECK(unit_price>=0),PRIMARY KEY(order_id,line_no),UNIQUE(order_id,offer_id));
CREATE TABLE event_type(event_type_id INTEGER PRIMARY KEY,event_code TEXT NOT NULL UNIQUE);
CREATE TABLE recommendation_run(run_id INTEGER PRIMARY KEY,session_id INTEGER NOT NULL REFERENCES user_session,strategy_code TEXT NOT NULL,strategy_version TEXT NOT NULL,generated_at INTEGER NOT NULL,history_cutoff INTEGER NOT NULL CHECK(history_cutoff<=generated_at));
CREATE TABLE recommendation_item(run_id INTEGER NOT NULL REFERENCES recommendation_run,product_id INTEGER NOT NULL REFERENCES product,rank_no INTEGER NOT NULL CHECK(rank_no>0),score REAL NOT NULL,reason_code TEXT NOT NULL,source_product_id INTEGER REFERENCES product,PRIMARY KEY(run_id,product_id),UNIQUE(run_id,rank_no));
CREATE TABLE event(event_id INTEGER PRIMARY KEY,session_id INTEGER NOT NULL REFERENCES user_session,event_type_id INTEGER NOT NULL REFERENCES event_type,product_id INTEGER NOT NULL REFERENCES product,occurred_at INTEGER NOT NULL,run_id INTEGER,FOREIGN KEY(run_id,product_id) REFERENCES recommendation_item(run_id,product_id),CHECK((event_type_id=3 AND run_id IS NOT NULL) OR (event_type_id<>3 AND run_id IS NULL)));
CREATE TRIGGER order_context BEFORE INSERT ON customer_order WHEN NEW.session_id IS NOT NULL BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM user_session s WHERE s.session_id=NEW.session_id AND s.user_id=NEW.user_id AND s.started_at<=NEW.ordered_at) THEN RAISE(ABORT,'Invalid order session') END;
END;
CREATE TRIGGER event_context BEFORE INSERT ON event BEGIN
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM user_session s WHERE s.session_id=NEW.session_id AND s.started_at<=NEW.occurred_at) THEN RAISE(ABORT,'Invalid event session') END;
 SELECT CASE WHEN NEW.run_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM recommendation_run r WHERE r.run_id=NEW.run_id AND r.session_id=NEW.session_id AND r.generated_at<=NEW.occurred_at) THEN RAISE(ABORT,'Invalid recommendation context') END;
END;
CREATE VIEW order_product AS SELECT DISTINCT o.order_id,o.user_id,o.session_id,o.ordered_at,f.product_id FROM customer_order o JOIN order_item i USING(order_id) JOIN offer f USING(offer_id) WHERE o.status='confirmed';
