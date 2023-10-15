import aiohttp


class AioHttp:
    session: aiohttp.ClientSession | None = None

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        if cls.session is None:
            cls.start()

        return cls.session

    @classmethod
    async def close(cls):
        if cls.session:
            await cls.session.close()
            cls.session = None

    @classmethod
    def start(cls):
        if cls.session is not None:
            return

        timeout = aiohttp.ClientTimeout(total=3)

        try:
            # aiodns를 설치해도 기본으로 AsyncResolver를 사용하지 않는다
            # Issue: https://github.com/aio-libs/aiohttp/issues/2228, https://github.com/aio-libs/aiohttp/issues/6836
            # 따라서 aiodns가 설치되어있는 경우에는 AsyncResolver를 사용하도록 설정한다
            import aiodns
        except ImportError as e:
            cls.session = aiohttp.ClientSession(timeout=timeout)
        else:
            connector = aiohttp.TCPConnector(resolver=aiohttp.AsyncResolver())
            cls.session = aiohttp.ClientSession(timeout=timeout, connector=connector)


async def get_http_session() -> aiohttp.ClientSession:
    return AioHttp.get_session()
