from typing import Any, Dict, Iterator, List, Optional, Union

import responses

from ..utils import slash_join


class RegisteredResponse:
    _url_map = {
        "auth": "https://auth.globus.org/",
        "nexus": "https://nexus.api.globusonline.org/",
        "transfer": "https://transfer.api.globus.org/v0.10",
        "search": "https://search.api.globus.org/",
        "gcs": "https://abc.xyz.data.globus.org/api",
        "groups": "https://groups.api.globus.org/v2/",
    }

    def __init__(
        self,
        *,
        path: str,
        service: Optional[str] = None,
        method: str = responses.GET,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        json: Union[None, List[Any], Dict[str, Any]] = None,
        body: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.service = service
        self.path = path
        if service:
            self.full_url = slash_join(self._url_map[service], path)
        else:
            self.full_url = path

        self.method = method
        self.json = json
        self.body = body

        if headers is None:
            headers = {"Content-Type": "application/json"}
        self.headers = headers

        self.metadata = metadata or {}
        self.kwargs = kwargs

    def add(self) -> "RegisteredResponse":
        kwargs: Dict[str, Any] = {
            "headers": self.headers,
            "match_querystring": None,
            **self.kwargs,
        }
        if self.json is not None:
            kwargs["json"] = self.json
        if self.body is not None:
            kwargs["body"] = self.body

        responses.add(self.method, self.full_url, **kwargs)
        return self


class ResponseSet:
    def __init__(
        self,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: RegisteredResponse,
    ) -> None:
        self.metadata = metadata
        self._data: Dict[str, RegisteredResponse] = {**kwargs}

    def register(self, case: str, value: RegisteredResponse) -> None:
        self._data[case] = value

    def lookup(self, case: str) -> RegisteredResponse:
        try:
            return self._data[case]
        except KeyError as e:
            raise Exception("did not find a matching registered response") from e

    def __bool__(self) -> bool:
        return bool(self._data)

    def __iter__(self) -> Iterator[RegisteredResponse]:
        return iter(self._data.values())

    def activate(self, case: str) -> RegisteredResponse:
        return self.lookup(case).add()

    def activate_all(self) -> "ResponseSet":
        for x in self:
            x.add()
        return self

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Dict[str, Any]],
    ) -> "ResponseSet":
        # constructor which expects native dicts and converts them to RegisteredResponse
        # objects, then puts them into the ResponseSet
        return cls(
            metadata=metadata, **{k: RegisteredResponse(**v) for k, v in data.items()}
        )
