from django.db import models

# Create your models here.
"""Mapeo de transformación de materia prima a un producto terminado (PRODUCCION, DETALLE_PRODUCCION)"""


# ---------------------------------MODELO PRODUCCION ---------------------------------
class Produccion(models.Model):
    # Enum tipo_estado_produccion de tu SQL
    class EstadoProduccion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_PROCESO = 'EN_PROCESO', 'En Proceso'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    # BIGSERIAL en Postgres -> BigAutoField en Django
    id_produccion = models.BigAutoField(primary_key=True, db_column='id_produccion')
    nombre_produccion = models.CharField(max_length=50, db_column='nombre_produccion')
    cant_produccion = models.CharField(max_length=50, db_column='categoria_produccion')
    cant_produccion = models.BigIntegerField(db_column='cant_produccion')
    descripcion_produccion = models.CharField(max_length=200, db_column='descripcion_produccion')

    # FK al Producto que se está fabricando (ej: Pan Blandito)
    id_producto_fk_produccion = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto_fk_produccion'
    )

    # FK al Usuario que supervisa la producción
    id_usuario_fk_produccion = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario_fk_produccion'
    )

    estado_produccion = models.CharField(
        max_length=20,
        choices=EstadoProduccion.choices,
        db_column='estado_produccion'
    )

    class Meta:
        managed = False
        db_table = 'produccion'

    def __str__(self):
        return f"{self.nombre_produccion} ({self.id_produccion})"


# ---------------------------------MODELO DETALLE PRODUCCION---------------------------------
class DetalleProduccion(models.Model):
    # BIGSERIAL en Postgres -> BigAutoField en Django
    id_detalle_produccion = models.BigAutoField(primary_key=True, db_column='id_detalle_produccion')

    # FK a la orden de Producción padre
    id_produccion_fk_det_produc = models.ForeignKey(
        Produccion,
        on_delete=models.CASCADE,
        db_column='id_produccion_fk_det_produc',
        related_name='insumos'
    )

    # FK a la Materia Prima que se consume (ej: Harina)
    id_materia_prima_fk_det_produc = models.ForeignKey(
        'inventario.MateriaPrima',
        on_delete=models.PROTECT,
        db_column='id_materia_prima_fk_det_produc'
    )

    # DECIMAL(10,2) en Postgres -> DecimalField en Django
    # Importante: max_digits es el total de números y decimal_places los que van tras la coma.
    cantidad_requerida = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column='cantidad_requerida'
    )

    class Meta:
        managed = False
        db_table = 'detalle_produccion'