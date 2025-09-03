from .domain import HealthCheckInterface
from .model import HealthCheckModel, HealthCheckEntityModel
from .enum import HealthCheckStatusEnum
from typing import List
from datetime import datetime
import os
import socket

class HealthCheckFactory:
    _healthItems: List[HealthCheckInterface]
    _health: HealthCheckModel

    def __init__(self) -> None:
        self._healthItems = list()

    def add(self, item: HealthCheckInterface) -> None:
        self._healthItems.append(item)

    def __startTimer__(self, entityTimer: bool) -> None:
        if entityTimer == True:
            self._entityStartTime = datetime.now()
        else:
            self._totalStartTime = datetime.now()

    def __stopTimer__(self, entityTimer: bool) -> None:
        if entityTimer == True:
            self._entityStopTime = datetime.now()
        else:
            self._totalStopTime = datetime.now()

    def __getTimeTaken__(self, entityTimer: bool) -> datetime:
        if entityTimer == True:
            return self._entityStopTime - self._entityStartTime
        return self._totalStopTime - self._totalStartTime

    def __dumpModel__(self, model: HealthCheckModel) -> str:
        """This goes and convert python objects to something a json object."""
        l = list()
        for i in model.entities:
            i.status = i.status.value
            i.timeTaken = str(i.timeTaken)
            l.append(dict(i))

        model.entities = l
        model.status = model.status.value
        model.totalTimeTaken = str(model.totalTimeTaken)
        model.host = model.host
        model.image = dict(model.image)

        return dict(model)

    def check(self) -> HealthCheckModel:
        health = HealthCheckModel()
        self.__startTimer__(False)
        for i in self._healthItems:
            # Generate the model
            if not hasattr(i, "_tags"):
                i._tags = list()
            if not hasattr(i, "_properties"):
                i._properties = dict()
            item = HealthCheckEntityModel(
                alias=i._alias, tags=i._tags if i._tags else [], properties=i._properties
            )

            # Track how long the entity took to respond
            self.__startTimer__(True)
            item.status = i.__checkHealth__()
            self.__stopTimer__(True)
            item.timeTaken = self.__getTimeTaken__(True)

            # if we have one dependency unhealthy, the service in unhealthy
            if item.status == HealthCheckStatusEnum.UNHEALTHY:
                health.status = HealthCheckStatusEnum.UNHEALTHY

            health.entities.append(item)
        self.__stopTimer__(False)
        health.totalTimeTaken = self.__getTimeTaken__(False)

        # extended with own properties
        health.host = socket.gethostname()
        
        version = os.getenv('VERSION', '?')
        build_number = os.getenv('BUILD_NO', '?')
        branch = os.getenv('BRANCH', '?')
        git_hash = os.getenv('GIT_HASH', '?')
        health.image = {
            'version': version,
            'buildNumber': build_number,
            'branch': branch,
            'gitHash': git_hash,
        }

        health = self.__dumpModel__(health)

        return health


class HealthCheckBase:
    def setConnectionUri(self, value: str) -> None:
        if value == "":
            raise Exception(f"{self._service} ConnectionUri is missing a value.")
        self._connectionUri = value

    def getConnectionUri(self) -> str:
        return self._connectionUri

    def setName(self, value: str) -> str:
        if not value:
            raise Exception("Missing a valid name.")
        self._name = value

    def getService(self) -> str:
        return self._service

    def getTags(self) -> List[str]:
        return self._tags
    
    def getProperties(self) -> dict:
        return self._properties

    def getAlias(self) -> str:
        return self._alias
