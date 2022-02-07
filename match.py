from time import time
import docker
import uuid
import os
import shutil

from db_interface import DBInterface


class Match:

    ERRORDRAW = 0
    BOT1 = 1
    BOT2 = 2

    def __init__(self, bot1, bot2, timestamp, db: DBInterface):
        self._bot1 = bot1
        self._bot2 = bot2
        self._timestamp = timestamp
        self._container = None
        self._result_file_name = self._get_hash()
        self._db = db
        self._parent_dir = os.path.dirname(__file__)
        self._client = docker.from_env()
    
    def run(self):
        full_path = os.path.join(self._parent_dir, f"temp/{str(self._timestamp)}")
        os.mkdir(full_path)
        
        self._db.download_bot_file(self._bot1, DBInterface.SEEKER, full_path)
        self._db.download_bot_file(self._bot2, DBInterface.HIDER, full_path)
        self._copy_game_files(full_path)

        command = f"python main.py {self._bot1}.py {self._bot2}.py {self._result_file_name}"

        try:
            response = self._client.containers.run("python",
                                                   command=command,
                                                   volumes=[f"./temp/{str(self._timestamp)}:/code"],
                                                   network_disabled=True,
                                                   mem_limit="500m",
                                                   cpu_count=1,
                                                   )        
        except docker.errors.ContainerError:
            print("Code execution failed - syntax error")
                    
    def _copy_game_files(self, destination):
        full_path = os.path.join(self._parent_dir, "game")
        for filename in os.listdir(full_path):
            file_path = os.path.join(full_path, filename)
            shutil.copyfile(file_path, f"{destination}/{filename}")

        # print(full_path, destination, flush=True)
        # shutil.copy(full_path, destination)
    
    def stop(self):
        self._container.kill()

    def is_finished(self):
        res = self.container.status == "exited"
        if res:
            self._client.containers.prune()
        return res

    def get_results(self):
        cat_exit_code, cat_output = self.container.exec_run("cat " + f"{self._result_file_name}.json")
        return cat_output

    def _get_hash(self):
        return str(uuid.uuid1())
