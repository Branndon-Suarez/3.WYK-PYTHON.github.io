from django.db import models

# --------------------------------- MODELOS DE RECETAS ---------------------------------

class Receta(models.Model):
    id_receta = models.AutoField(primary_key=True, db_column='id_receta')
    nombre_receta = models.CharField(max_length=100, db_column='nombre_receta')
    descripcion_receta = models.CharField(max_length=255, blank=True, null=True, db_column='descripcion_receta')
    cantidad_base = models.BigIntegerField(default=1, db_column='cantidad_base')

    id_producto_fk_receta = models.OneToOneField(
        'inventario.Producto',
        on_delete=models.CASCADE,
        db_column='id_producto_fk_receta'
    )

    id_usuario_fk_receta = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario_fk_receta'
    )

    estado_receta = models.BooleanField(default=True, db_column='estado_receta')

    class Meta:
        managed = False
        db_table = 'receta'

    def __str__(self):
        return self.nombre_receta


class DetalleReceta(models.Model):
    id_detalle_receta = models.AutoField(primary_key=True, db_column='id_detalle_receta')

    # Ajustado a string para mantener consistencia con el resto de tus modelos
    id_receta_fk_det_rec = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.CASCADE,
        db_column='id_receta_fk_det_rec',
        related_name='insumos_receta'
    )

    id_materia_prima_fk_det_rec = models.ForeignKey(
        'inventario.MateriaPrima',
        on_delete=models.PROTECT,
        db_column='id_materia_prima_fk_det_rec'
    )

    cantidad_insumo_base = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        db_column='cantidad_insumo_base'
    )

    class Meta:
        managed = False
        db_table = 'detalle_receta'