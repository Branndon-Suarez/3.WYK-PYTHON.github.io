from django.db import models

# --------------------------------- MODELO PRODUCCION ---------------------------------
class Produccion(models.Model):
    class EstadoProduccion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_PROCESO = 'EN_PROCESO', 'En Proceso'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    id_produccion = models.BigAutoField(primary_key=True, db_column='id_produccion')
    nombre_produccion = models.CharField(max_length=50, db_column='nombre_produccion')
    fecha_hora_produccion = models.DateTimeField(db_column='fecha_hora_produccion')
    fecha_cambio_estado = models.DateTimeField(blank=True, null=True, db_column='fecha_cambio_estado')
    categoria_produccion = models.CharField(max_length=50, db_column='categoria_produccion')
    cant_produccion = models.BigIntegerField(db_column='cant_produccion')
    descripcion_produccion = models.CharField(max_length=200, db_column='descripcion_produccion')

    id_producto_fk_produccion = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto_fk_produccion'
    )

    # Relación a Receta usando el método de string
    id_receta_fk_produccion = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.PROTECT,
        db_column='id_receta_fk_produccion'
    )

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


# --------------------------------- MODELO DETALLE PRODUCCION ---------------------------------
class DetalleProduccion(models.Model):
    id_detalle_produccion = models.BigAutoField(primary_key=True, db_column='id_detalle_produccion')

    # Ajustado a string 'produccion.Produccion' para uniformidad total
    id_produccion_fk_det_produc = models.ForeignKey(
        'produccion.Produccion',
        on_delete=models.CASCADE,
        db_column='id_produccion_fk_det_produc',
        related_name='insumos'
    )

    id_materia_prima_fk_det_produc = models.ForeignKey(
        'inventario.MateriaPrima',
        on_delete=models.PROTECT,
        db_column='id_materia_prima_fk_det_produc'
    )

    cantidad_requerida = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        db_column='cantidad_requerida'
    )

    class Meta:
        managed = False
        db_table = 'detalle_produccion'