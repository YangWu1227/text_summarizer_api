from typing import Annotated, Dict, List

from fastapi import APIRouter, BackgroundTasks, Path

from app.api import crud
from app.api.custom_exceptions import SummaryNotFoundException
from app.models.pydantic import (
    SummaryPayloadSchema,
    SummaryResponseSchema,
    SummaryUpdatePayloadSchema,
)
from app.models.tortoise import SummarySchema
from app.summarizer import generate_summary

router = APIRouter()


@router.post("/", response_model=SummaryResponseSchema, status_code=201)
async def create_summary(
    payload: SummaryPayloadSchema, background_tasks: BackgroundTasks
) -> SummaryResponseSchema:
    """
    Create a new summary based on the provided payload.

    Parameters
    ----------
    payload : SummaryPayloadSchema
        The payload containing a valid url required to create the new summary.
    background_tasks : BackgroundTasks
        A collection of background tasks that will be called after a response has been sent to the client.

    Returns
    -------
    SummaryResponseSchema
        The newly created summary's response, including the `url`, `id`, `summarizer_specifier`, and `sentence_count`.
    """
    summary_id = await crud.post(payload)
    # Generate summary as a background task
    background_tasks.add_task(
        generate_summary,
        summary_id,
        str(payload.url),
        payload.summarizer_specifier,
        int(payload.sentence_count),
    )
    response = SummaryResponseSchema(
        url=payload.url,
        id=summary_id,
        summarizer_specifier=payload.summarizer_specifier,
        sentence_count=payload.sentence_count,
    )
    return response


@router.get("/{id}/", response_model=SummarySchema)
async def read_summary(id: Annotated[int, Path(title="The ID of the text summary to query", gt=0)]) -> SummarySchema:  # type: ignore
    """
    Retrieve a single summary based on its ID (i.e., primary key).

    Parameters
    ----------
    id : int
        The ID of the text summary to query; must be greater than 0.

    Returns
    -------
    SummarySchema
        The retrieved summary object.

    Raises
    ------
    SummaryNotFoundException
        If the summary with the given ID is not found.
    """
    summary = await crud.get(id)
    # Raise a 404 Not Found error if an id is non-existent
    if not summary:
        raise SummaryNotFoundException
    return summary


@router.get("/", response_model=List[SummarySchema])  # type: ignore
async def read_all_summaries() -> List[SummarySchema]:  # type: ignore
    """
    Retrieve all summaries.

    Returns
    -------
    List[SummarySchema]
        A list of all the summaries.
    """
    return await crud.get_all()


@router.delete("/{id}/", response_model=SummarySchema)
async def remove_summary(
    id: Annotated[int, Path(title="The ID of the text summary to delete", gt=0)]
) -> SummarySchema:  # type: ignore
    """
    Delete a single summary based on its ID (i.e., primary key).

    Parameters
    ----------
    id : int
        The ID of the summary to delete; must be greater than 0.

    Returns
    -------
    SummarySchema
        The retrieved summary response containing an ID and url.

    Raises
    ------
    SummaryNotFoundException
        If the summary with the given ID is not found.
    """
    summary = await crud.get(id)
    # Raise a 404 Not Found error if an id is non-existent
    if not summary:
        raise SummaryNotFoundException
    # Delete the record
    await crud.delete(id)
    # Return the summary record that was deleted
    return summary


@router.put("/{id}/", response_model=SummarySchema)
async def update_summary(
    id: Annotated[int, Path(title="The ID of the text summary to update", gt=0)],
    payload: SummaryUpdatePayloadSchema,
) -> SummarySchema:  # type:ignore
    """
    Update a text summary by its ID. Both the URL and the summary text are updated based on the provided payload.

    Parameters
    ----------
    id : int
        The ID of the text summary to update; must be greater than 0.
    payload : SummaryUpdatePayloadSchema
        The data to update the summary with, including the new URL and summary text.

    Returns
    -------
    SummarySchema
        The updated summary object if the update is successful.

    Raises
    ------
    SummaryNotFoundException
        If no summary with the specified ID exists.
    """
    summary = await crud.put(id, payload)
    # Raise a 404 Not Found error if an id is non-existent
    if not summary:
        raise SummaryNotFoundException
    return summary
