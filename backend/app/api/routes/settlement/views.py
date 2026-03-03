import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.api.routes.settlement.schemas import (
    GenerateRemittancesResponse,
    RemittanceGenerated,
    WorkLogListItem,
    WorkLogListResponse,
)
from app.models import Adjustment, Remittance, TimeSegment, User, WorkLog

logger = logging.getLogger(__name__)

router = APIRouter(tags=["settlement"])

REMITTANCE_SUCCESS = "SUCCESS"
REMITTANCE_FAILED = "FAILED"
REMITTANCE_CANCELLED = "CANCELLED"


def _worklog_amount(session: Session, wl_id: UUID) -> float:
    segs = session.exec(
        select(TimeSegment).where(TimeSegment.worklog_id == wl_id)
    ).all()
    seg_sum = sum(s.hours * s.rate for s in segs)
    adjs = session.exec(
        select(Adjustment).where(Adjustment.worklog_id == wl_id)
    ).all()
    adj_sum = sum(a.amount for a in adjs)
    return seg_sum + adj_sum


def _is_eligible_worklog(session: Session, wl: WorkLog) -> bool:
    if wl.remittance_id is None:
        return True
    r = session.get(Remittance, wl.remittance_id)
    if r is None:
        return True
    return r.status in (REMITTANCE_FAILED, REMITTANCE_CANCELLED)


@router.post(
    "/generate-remittances-for-all-users",
    response_model=GenerateRemittancesResponse,
)
def generate_remittances_for_all_users(session: SessionDep) -> GenerateRemittancesResponse:
    users = session.exec(select(User)).all()
    created: list[RemittanceGenerated] = []
    for u in users:
        try:
            wls = session.exec(
                select(WorkLog).where(WorkLog.user_id == u.id)
            ).all()
            eligible = [wl for wl in wls if _is_eligible_worklog(session, wl)]
            if not eligible:
                continue
            t = 0.0
            for wl in eligible:
                t += _worklog_amount(session, wl.id)
            r = Remittance(
                user_id=u.id,
                amount=t,
                status=REMITTANCE_SUCCESS,
            )
            session.add(r)
            session.commit()
            session.refresh(r)
            for wl in eligible:
                wl.remittance_id = r.id
                session.add(wl)
            session.commit()
            created.append(
                RemittanceGenerated(
                    id=r.id,
                    user_id=r.user_id,
                    amount=r.amount,
                    status=r.status,
                    created_at=r.created_at,
                )
            )
        except Exception as e:
            logger.error("Failed to generate remittance for user %s: %s", u.id, e)
            continue
    return GenerateRemittancesResponse(remittances=created)


@router.get(
    "/list-all-worklogs",
    response_model=WorkLogListResponse,
)
def list_all_worklogs(
    session: SessionDep,
    remittanceStatus: Literal["REMITTED", "UNREMITTED"] | None = Query(
        default=None, description="Filter by remittance status"
    ),
) -> WorkLogListResponse:
    stmt = select(WorkLog)
    wls = session.exec(stmt).all()
    if remittanceStatus == "REMITTED":
        wls = [
            wl
            for wl in wls
            if wl.remittance_id is not None
            and (r := session.get(Remittance, wl.remittance_id)) is not None
            and r.status == REMITTANCE_SUCCESS
        ]
    elif remittanceStatus == "UNREMITTED":
        wls = [
            wl
            for wl in wls
            if wl.remittance_id is None
            or (
                (r := session.get(Remittance, wl.remittance_id)) is not None
                and r.status in (REMITTANCE_FAILED, REMITTANCE_CANCELLED)
            )
        ]
    items: list[WorkLogListItem] = []
    for wl in wls:
        amt = _worklog_amount(session, wl.id)
        items.append(
            WorkLogListItem(
                id=wl.id,
                user_id=wl.user_id,
                remittance_id=wl.remittance_id,
                amount=round(amt, 2),
                created_at=wl.created_at,
            )
        )
    return WorkLogListResponse(data=items, count=len(items))
