import argparse
import sys

from core.system import System


class App:
    def __init__(self, args):
        self.args = args
        # [edit] pass auto_login to System
        self.system = System(
            reset_database=self.args.reset_db, auto_login=self.args.auto_login
        )

    def run(self):
        self.system.run()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SafeHome Application")
    parser.add_argument(
        "--reset-db",
        "--reset_db",
        dest="reset_db",
        action="store_true",
        help="Reset database on startup",
    )
    parser.add_argument(
        "--auto-login",
        "--auto_login",
        dest="auto_login",
        action="store_true",
        help="Automatically turn on system and login as admin",
    )
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args(sys.argv[1:])
    app = App(args=args)
    app.run()
