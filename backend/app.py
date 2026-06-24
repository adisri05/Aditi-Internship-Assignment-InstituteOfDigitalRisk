from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.database import DEFAULT_DB_PATH, connect, initialize_database
from backend.models import RankingEntry, SummaryResponse, TransactionRequest, TransactionResult
from backend.repository import TransactionRepository, to_summary_response, to_transaction_response


def create_app(db_path: Path | str = DEFAULT_DB_PATH) -> FastAPI:
    setup_connection = connect(db_path)
    initialize_database(setup_connection)
    setup_connection.close()

    app = FastAPI(title="Transaction Ranking Service", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_repository():
        connection = connect(db_path)
        try:
            yield TransactionRepository(connection)
        finally:
            connection.close()

    @app.post("/transaction", response_model=TransactionResult, status_code=201)
    def post_transaction(
        payload: TransactionRequest,
        repository=Depends(get_repository),
    ) -> TransactionResult:
        try:
            transaction, summary, duplicate = repository.create_transaction(payload)
        except LookupError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return TransactionResult(
            transaction=to_transaction_response(transaction, duplicate),
            summary=to_summary_response(summary),
        )

    @app.get("/summary/{user_id}", response_model=SummaryResponse)
    def get_summary(
        user_id: Annotated[str, ApiPath(pattern=r"^[A-Za-z0-9_-]{3,64}$")],
        repository=Depends(get_repository),
    ) -> SummaryResponse:
        return to_summary_response(repository.get_summary(user_id))

    @app.get("/ranking", response_model=list[RankingEntry])
    def get_ranking(
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
        repository=Depends(get_repository),
    ) -> list[dict]:
        return repository.get_ranking(limit)

    return app


app = create_app()
