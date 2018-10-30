CREATE TABLE log(
  id integer UNIQUE PRIMARY KEY AUTOINCREMENT,
  object_type char(3) NOT NULL DEFAULT 'sys',
  object_id integer NOT NULL DEFAULT 0,
  message text NOT NULL
);
