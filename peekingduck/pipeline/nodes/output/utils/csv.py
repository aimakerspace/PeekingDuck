# Copyright 2021 AI Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utils for CSV logging
"""
import csv
from datetime import datetime
from typing import Any, Dict, List

class CSVLogger:

    def __init__(self,filepath: str,headers: List[str],logging_interval: int=1) -> None:
        headers.insert(0,"Time")
        self.headers = headers
        self.filepath = filepath
        self.logging_interval = logging_interval
        self.csv_file = open(self.filepath, mode="a+",newline='')
        self.writer = csv.DictWriter(self.csv_file, fieldnames=self.headers)
        self.last_write = datetime.now()

        # if file is empty write header
        if self.csv_file.tell() == 0: self.writer.writeheader()

    def write(self,data_pool: Dict[str, Any],specific_data: List[str]) -> None:
        content = {k:v for k,v in data_pool.items() if k in specific_data}
        curr_time = datetime.now()
        time_str = curr_time.strftime("%H:%M:%S")
        content.update({"Time":time_str})

        if (curr_time - self.last_write).seconds >= self.logging_interval:
            self.writer.writerow(content)
            self.last_write = curr_time

    def __del__(self) -> None:
        self.csv_file.close()
