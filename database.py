import sqlite3

class quotaDb():
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        sql_create = """
            CREATE TABLE IF NOT EXISTS userquota (
                user TEXT PRIMARY KEY,
                used INTEGER DEFAULT 0,
                soft_limit INTEGER DEFAULT 0,
                hard_limit INTEGER DEFAULT 0,
                state INTEGER DEFAULT 0,
                alert INTEGER DEFAULT 0
            )"""    # state: 0: not exceeded, 1: exceed soft limit, 2: exceed hard limit
                    # alert: 0: no alert sent, 1: soft alert sent, 2: hard alert sent
        self.cursor.execute(sql_create)
        self.connection.commit()

        self.sql_update = "INSERT INTO userquota (user, used, soft_limit, hard_limit, state) " \
                          "VALUES (?, ?, ?, ?, ?) ON CONFLICT(user) DO UPDATE SET " \
                          "used = ?, soft_limit = ?, hard_limit = ?, state = ?"
        self.sql_alert = "UPDATE userquota SET alert = state WHERE user = ?"
        self.sql_query = "SELECT * FROM userquota"
        self.sql_need_alert = "SELECT * FROM userquota WHERE alert < state"
        self.sql_reset = "UPDATE userquota SET alert = 0 WHERE alert > 0 and state = 0"

    def update(self, info_list):
        """
        Update users' quota info in DB, create if not exists.
        Args:
            info_list: [(user, used, soft_limit, hard_limit, state, user), ...]
        """
        self.cursor.executemany(self.sql_update, info_list)
        self.commit()

    def get_alert_list(self):
        """
        Get a list of over-quota users who need alerts.
        """
        rows = self.cursor.execute(self.sql_need_alert).fetchall()
        return rows

    def update_alert(self, user):
        """
        Update alert status of a user in DB.
        Needs manual commit.
        """
        self.cursor.execute(self.sql_alert, (user,))

    def reset_alert(self):
        """
        Reset alert status for users who is back under quota.
        """
        self.cursor.execute(self.sql_reset)
        self.commit()

    def query_all(self):
        """
        Get all users' quota info from DB.
        """
        rows = self.cursor.execute(self.sql_query).fetchall()
        return rows

    def truncate(self):
        """
        Clear all users' quota info in DB.
        """
        self.cursor.execute("DELETE FROM userquota")
        self.commit()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()


if __name__ == '__main__':
    db = quotaDb()
    db.truncate()