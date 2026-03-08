from django.db import models

# Create your models here.
"""El punto de venta (VENTA, DETALLE_VENTA)"""


# ---------------------------------MODELO VENTA---------------------------------

class Venta(models.Model):
    # Enums de tipo_estado_pedido
    class EstadoPedido(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PREPARANDO = 'PREPARANDO', 'Preparando'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    # Enums de tipo_estado_pago
    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADA = 'PAGADA', 'Pagada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    # BIGSERIAL en Postgres -> BigAutoField en Django
    id_venta = models.BigAutoField(primary_key=True, db_column='id_venta')
    fecha_hora_venta = models.DateTimeField(db_column='fecha_hora_venta')
    total_venta = models.BigIntegerField(db_column='total_venta')
    numero_mesa = models.IntegerField(blank=True, null=True, db_column='numero_mesa')
    descripcion = models.CharField(max_length=200, blank=True, null=True, db_column='descripcion')

    # FK a Usuario (Quién realizó la venta)
    id_usuario_fk_venta = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario_fk_venta'
    )

    estado_pedido = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        db_column='estado_pedido'
    )
    estado_pago = models.CharField(
        max_length=20,
        choices=EstadoPago.choices,
        db_column='estado_pago'
    )

    class Meta:
        managed = False
        db_table = 'venta'

    def __str__(self):
        return f"Venta {self.id_venta} - {self.total_venta}"


# ---------------------------------MODELO DETALLE VENTA---------------------------------
class DetalleVenta(models.Model):
    # SERIAL en Postgres -> AutoField en Django
    id_detalle_venta = models.AutoField(primary_key=True, db_column='id_detalle_venta')
    cantidad = models.BigIntegerField(db_column='cantidad')
    sub_total = models.BigIntegerField(db_column='sub_total')

    # FK a la Venta (Padre)
    # Usamos CASCADE aquí porque si se borra la cabecera de la venta,
    # sus detalles no tienen sentido solos (aunque usualmente no borrarás ventas).
    id_venta_fk_det_venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        db_column='id_venta_fk_det_venta',
        related_name='detalles'
    )

    # FK al Producto (De la app inventario)
    id_producto_fk_det_venta = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto_fk_det_venta'
    )

    class Meta:
        managed = False
        db_table = 'detalle_venta'