from django.db import models


# ---------------------------------MODELO PROVEEDOR---------------------------------
class Proveedor(models.Model):
    # Usamos BigIntegerField porque en SQL es BIGINT (Cédula)
    cedula_proveedor = models.BigIntegerField(primary_key=True, db_column='cedula_proveedor')
    lugar_expedicion = models.CharField(max_length=50, db_column='lugar_expedicion')
    nombre_proveedor = models.CharField(max_length=50, db_column='nombre_proveedor')
    marca = models.CharField(max_length=50, db_column='marca')
    tel_proveedor = models.BigIntegerField(unique=True, db_column='tel_proveedor')
    email_proveedor = models.EmailField(max_length=50, unique=True, db_column='email_proveedor')
    estado_proveedor = models.BooleanField(db_column='estado_proveedor')

    id_usuario_fk_proveedor = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario_fk_proveedor'
    )

    class Meta:
        managed = False
        db_table = 'proveedor'

    def __str__(self):
        return f"{self.nombre_proveedor} - {self.marca}"


# ---------------------------------MODELO COMPRA---------------------------------
class Compra(models.Model):
    class TipoCompra(models.TextChoices):
        # Ajustado para ser coherente con los tipos comunes de compra
        MATERIA_PRIMA = 'MATERIA PRIMA', 'Materia Prima'
        PRODUCTO_TERMINADO = 'PRODUCTO TERMINADO', 'Producto Terminado'

    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADA = 'PAGADA', 'Pagada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    id_compra = models.BigAutoField(primary_key=True, db_column='id_compra')
    fecha_hora_compra = models.DateTimeField(db_column='fecha_hora_compra')
    tipo = models.CharField(max_length=20, choices=TipoCompra.choices, db_column='tipo')
    total_compra = models.BigIntegerField(db_column='total_compra')
    descripcion_compra = models.CharField(max_length=200, blank=True, null=True, db_column='descripcion_compra')

    # RELACIÓN CON PROVEEDOR (Nueva según tu SQL)
    id_proveedor_fk_compra = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column='id_proveedor_fk_compra'
    )

    # FK al Usuario que registró la compra
    id_usuario_fk_compra = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario_fk_compra'
    )

    estado_factura_compra = models.CharField(
        max_length=20,  # Aumentado un poco por seguridad de los ENUMS
        choices=EstadoPago.choices,
        db_column='estado_factura_compra'
    )

    class Meta:
        managed = False
        db_table = 'compra'

    def __str__(self):
        return f"Compra #{self.id_compra} - {self.id_proveedor_fk_compra.nombre_proveedor}"


# ---------------------------------MODELO DETALLE COMPRA MATERIA PRIMA---------------------------------
class DetalleCompraMateriaPrima(models.Model):
    id_det_compra_mat_prim = models.AutoField(primary_key=True, db_column='id_det_compra_mat_prim')

    # DECIMAL(10,3) para mermas o compras exactas
    cantidad_mat_prima_comprada = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        db_column='cantidad_mat_prima_comprada'
    )
    sub_total_mat_prima_comprada = models.BigIntegerField(db_column='sub_total_mat_prima_comprada')

    id_compra_fk_det_compra_mat_prima = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        db_column='id_compra_fk_det_compra_mat_prima'
    )
    id_mat_prima_fk_det_compra_mat_prima = models.ForeignKey(
        'inventario.MateriaPrima',
        on_delete=models.PROTECT,
        db_column='id_mat_prima_fk_det_compra_mat_prima'
    )
    estado_det_compra_mat_prima = models.BooleanField(db_column='estado_det_compra_mat_prima')

    class Meta:
        managed = False
        db_table = 'detalle_compra_materia_prima'


# ---------------------------------MODELO DETALLE COMPRA PRODUCTO---------------------------------
class DetalleCompraProducto(models.Model):
    id_det_compra_prod = models.AutoField(primary_key=True, db_column='id_det_compra_prod')
    cantidad_prod_comprado = models.BigIntegerField(db_column='cantidad_prod_comprado')
    sub_total_prod_comprado = models.BigIntegerField(db_column='sub_total_prod_comprado')

    id_compra_fk_det_compra_prod = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        db_column='id_compra_fk_det_compra_prod'
    )
    id_prod_fk_det_compra_prod = models.ForeignKey(
        'inventario.Producto',
        on_delete=models.PROTECT,
        db_column='id_prod_fk_det_compra_prod'
    )
    estado_det_compra_prod = models.BooleanField(db_column='estado_det_compra_prod')

    class Meta:
        managed = False
        db_table = 'detalle_compra_producto'