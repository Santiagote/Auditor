import logging
from celery import shared_task
from .metrics_engine import calculate_all

logger = logging.getLogger(__name__)


@shared_task
def recalculate_metrics():
    logger.info("Iniciando recálculo programado de métricas ISO 25010")
    calculate_all()
    logger.info("Recálculo completado")
    return True
