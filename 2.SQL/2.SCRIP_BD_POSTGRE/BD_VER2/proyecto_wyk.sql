
-- 1. Crear la base de datos (Ejecutar por separado si es necesario)
-- CREATE DATABASE proyecto_wyk;

-- 2. Definición de tipos ENUM (Postgres requiere crearlos primero)
CREATE TYPE tipo_clasificacion AS ENUM ('EMPLEADO', 'ADMINISTRADOR');
CREATE TYPE tipo_prioridad AS ENUM ('BAJA', 'MEDIA', 'ALTA');
CREATE TYPE tipo_estado_tarea AS ENUM ('PENDIENTE', 'COMPLETADA', 'CANCELADA');
CREATE TYPE tipo_producto AS ENUM ('PANADERIA', 'PASTELERIA', 'ASEO');
CREATE TYPE tipo_estado_pedido AS ENUM ('PENDIENTE', 'PREPARANDO', 'ENTREGADO', 'CANCELADO');
CREATE TYPE tipo_estado_pago AS ENUM ('PENDIENTE', 'PAGADA', 'CANCELADA');
CREATE TYPE tipo_ajuste AS ENUM ('DAÑADO', 'ROBO', 'PERDIDA', 'CADUCADO', 'MUESTRA');
CREATE TYPE tipo_ajuste_mat AS ENUM ('DAÑADO', 'ROBO', 'PERDIDA', 'CADUCADO');
CREATE TYPE tipo_compra AS ENUM ('MATERIA PRIMA', 'PRODUCTO TERMINADO');
CREATE TYPE tipo_estado_produccion AS ENUM ('PENDIENTE', 'EN_PROCESO', 'FINALIZADA', 'CANCELADA');

-- 3. Creación de tablas
CREATE TABLE rol(
    id_rol SERIAL PRIMARY KEY,
    rol VARCHAR(50) NOT NULL,
    clasificacion tipo_clasificacion NOT NULL,
    estado_rol BOOLEAN NOT NULL
);

CREATE TABLE usuario(
    id_usuario SERIAL PRIMARY KEY,
    num_doc BIGINT UNIQUE NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    password_usuario VARCHAR(150) NOT NULL,
    tel_usuario BIGINT NOT NULL,
    email_usuario VARCHAR(50) UNIQUE NOT NULL,
    fecha_registro TIMESTAMP NOT NULL,
    rol_fk_usuario INT NOT NULL,
    estado_usuario BOOLEAN NOT NULL,

    -- CAMPOS NUEVOS PARA COMPATIBILIDAD CON DJANGO:
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    CONSTRAINT rol_fk_usuario FOREIGN KEY (rol_fk_usuario) REFERENCES rol (id_rol)
);

CREATE TABLE tarea(
    id_tarea SERIAL PRIMARY KEY,
    tarea VARCHAR(100) NOT NULL,
    categoria VARCHAR(80) NOT NULL,
    descripcion VARCHAR(250) NULL,
    tiempo_estimado_horas REAL NOT NULL,
    prioridad tipo_prioridad NOT NULL,
    estado_tarea tipo_estado_tarea NOT NULL,
    usuario_asignado_fk INT NOT NULL,
    usuario_creador_fk INT NOT NULL,
    CONSTRAINT usuario_asignado_fk FOREIGN KEY(usuario_asignado_fk) REFERENCES usuario (id_usuario),
    CONSTRAINT usuario_creador_fk FOREIGN KEY(usuario_creador_fk) REFERENCES usuario(id_usuario)
);

CREATE TABLE producto(
    id_producto BIGINT PRIMARY KEY NOT NULL,
    nombre_producto VARCHAR(50) UNIQUE NOT NULL,
    valor_unitario_producto BIGINT NOT NULL,
    cant_exist_producto BIGINT NOT NULL,
    fecha_vencimiento_producto DATE NOT NULL,
    tipo_producto tipo_producto NOT NULL,
    id_usuario_fk_producto INT NOT NULL,
    estado_producto BOOLEAN NOT NULL,
    CONSTRAINT id_usuario_fk_producto FOREIGN KEY (id_usuario_fk_producto) REFERENCES usuario (id_usuario)
);

CREATE TABLE venta(
    id_venta BIGSERIAL PRIMARY KEY,
    fecha_hora_venta TIMESTAMP NOT NULL,
    total_venta BIGINT NOT NULL,
    numero_mesa INT NULL,
    descripcion VARCHAR(200) NULL,
    id_usuario_fk_venta INT NOT NULL,
    estado_pedido tipo_estado_pedido NOT NULL,
    estado_pago tipo_estado_pago NOT NULL,
    CONSTRAINT id_usuario_fk_venta FOREIGN KEY (id_usuario_fk_venta) REFERENCES usuario (id_usuario)
);

CREATE TABLE detalle_venta(
    id_detalle_venta SERIAL PRIMARY KEY,
    cantidad BIGINT NOT NULL,
    sub_total BIGINT NOT NULL,
    id_venta_fk_det_venta BIGINT NOT NULL,
    id_producto_fk_det_venta BIGINT NOT NULL,
    CONSTRAINT id_venta_fk_det_venta FOREIGN KEY (id_venta_fk_det_venta) REFERENCES venta (id_venta),
    CONSTRAINT id_producto_fk_det_venta FOREIGN KEY (id_producto_fk_det_venta) REFERENCES producto (id_producto)
);

CREATE TABLE ajuste_inventario(
    id_ajuste SERIAL PRIMARY KEY,
    fecha_ajuste TIMESTAMP NOT NULL,
    tipo_ajuste tipo_ajuste NOT NULL,
    cantidad_ajustada INT NOT NULL,
    descripcion VARCHAR(200) NULL,
    id_prod_fk_ajuste_inventario BIGINT NOT NULL,
    id_usuario_fk_ajuste_inventario INT NOT NULL,
    CONSTRAINT id_prod_fk_ajuste_inventario FOREIGN KEY (id_prod_fk_ajuste_inventario) REFERENCES producto (id_producto),
    CONSTRAINT id_usuario_fk_ajuste_inventario FOREIGN KEY (id_usuario_fk_ajuste_inventario) REFERENCES usuario (id_usuario)
);

CREATE TABLE materia_prima(
    id_materia_prima BIGSERIAL PRIMARY KEY,
    nombre_materia_prima VARCHAR(50) NOT NULL,
    valor_unitario_mat_prima BIGINT NOT NULL,
    fecha_vencimiento_materia_prima DATE NOT NULL,
    cantidad_exist_materia_prima BIGINT NOT NULL,
    presentacion_materia_prima VARCHAR(50) NOT NULL,
    descripcion_materia_prima VARCHAR(200) NOT NULL,
    id_usuario_fk_materia_prima INT NOT NULL,
    estado_materia_prima BOOLEAN NOT NULL,
    CONSTRAINT id_usuario_fk_materia_prima FOREIGN KEY (id_usuario_fk_materia_prima) REFERENCES usuario (id_usuario)
);

CREATE TABLE ajuste_materia_prima(
    id_ajus_mat SERIAL PRIMARY KEY,
    fecha_ajus_mat TIMESTAMP NOT NULL,
    tipo_ajus_mat tipo_ajuste_mat NOT NULL,
    cantidad_ajustada_mat INT NOT NULL,
    id_mat_fk_ajuste_mat BIGINT NOT NULL,
    id_usuario_fk_ajuste_mat INT NOT NULL,
    CONSTRAINT id_mat_fk_ajuste_mat FOREIGN KEY (id_mat_fk_ajuste_mat) REFERENCES materia_prima (id_materia_prima),
    CONSTRAINT id_usuario_fk_ajuste_mat FOREIGN KEY (id_usuario_fk_ajuste_mat) REFERENCES usuario (id_usuario)
);

CREATE TABLE compra(
    id_compra BIGSERIAL PRIMARY KEY,
    fecha_hora_compra TIMESTAMP NOT NULL,
    tipo tipo_compra NOT NULL,
    total_compra BIGINT NOT NULL,
    nombre_proveedor VARCHAR(50) NOT NULL,
    marca VARCHAR(50) NOT NULL,
    tel_proveedor BIGINT UNIQUE NOT NULL,
    email_proveedor VARCHAR(50) UNIQUE NOT NULL,
    descripcion_compra VARCHAR(200) NULL,
    id_usuario_fk_compra INT NOT NULL,
    estado_factura_compra tipo_estado_pago NOT NULL,
    CONSTRAINT id_usuario_fk_compra FOREIGN KEY (id_usuario_fk_compra) REFERENCES usuario (id_usuario)
);

CREATE TABLE detalle_compra_materia_prima(
    id_det_compra_mat_prim SERIAL PRIMARY KEY,
    cantidad_mat_prima_comprada BIGINT NOT NULL,
    sub_total_mat_prima_comprada BIGINT NOT NULL,
    id_compra_fk_det_compra_mat_prima BIGINT NOT NULL,
    id_mat_prima_fk_det_compra_mat_prima BIGINT NOT NULL,
    estado_det_compra_mat_prima BOOLEAN NOT NULL,
    CONSTRAINT id_compra_fk_det_compra_mat_prima FOREIGN KEY (id_compra_fk_det_compra_mat_prima) REFERENCES compra (id_compra),
    CONSTRAINT id_mat_prima_fk_det_compra_mat_prima FOREIGN KEY (id_mat_prima_fk_det_compra_mat_prima) REFERENCES materia_prima (id_materia_prima)
);

CREATE TABLE detalle_compra_producto(
    id_det_compra_prod SERIAL PRIMARY KEY,
    cantidad_prod_comprado BIGINT NOT NULL,
    sub_total_prod_comprado BIGINT NOT NULL,
    id_compra_fk_det_compra_prod BIGINT NOT NULL,
    id_prod_fk_det_compra_prod BIGINT NOT NULL,
    estado_det_compra_prod BOOLEAN NOT NULL,
    CONSTRAINT id_compra_fk_det_compra_prod FOREIGN KEY (id_compra_fk_det_compra_prod) REFERENCES compra (id_compra),
    CONSTRAINT id_prod_fk_det_compra_prod FOREIGN KEY (id_prod_fk_det_compra_prod) REFERENCES producto (id_producto)
);

CREATE TABLE produccion(
    id_produccion BIGSERIAL PRIMARY KEY,
    nombre_produccion VARCHAR(50) NOT NULL,
    categoria_produccion VARCHAR(50) NOT NULL,
    cant_produccion BIGINT NOT NULL,
    descripcion_produccion VARCHAR(200) NOT NULL,
    id_producto_fk_produccion BIGINT NOT NULL,
    id_usuario_fk_produccion INT NOT NULL,
    estado_produccion tipo_estado_produccion NOT NULL,
    CONSTRAINT id_producto_fk_produccion FOREIGN KEY (id_producto_fk_produccion) REFERENCES producto (id_producto),
    CONSTRAINT id_usuario_fk_produccion FOREIGN KEY (id_usuario_fk_produccion) REFERENCES usuario (id_usuario)
);

CREATE TABLE detalle_produccion(
    id_detalle_produccion BIGSERIAL PRIMARY KEY,
    id_produccion_fk_det_produc BIGINT NOT NULL,
    id_materia_prima_fk_det_produc BIGINT NOT NULL,
    cantidad_requerida DECIMAL(10,2) NOT NULL,
    CONSTRAINT id_produccion_fk_det_produc FOREIGN KEY (id_produccion_fk_det_produc) REFERENCES produccion(id_produccion),
    CONSTRAINT id_materia_prima_fk_det_produc FOREIGN KEY (id_materia_prima_fk_det_produc) REFERENCES materia_prima(id_materia_prima)
);