#include "qemu/osdep.h"
#include "hw/pci/pci.h"
#include "hw/pci/msi.h"
#include "hw/pci/msix.h"
#include "hw/hw.h"
#include "hw/qdev-properties.h"
#include "migration/vmstate.h"
#include "net/net.h"
#include "sysemu/sysemu.h"
#include "sysemu/dma.h"
#include "qemu/module.h"
#include "qemu/range.h"
#include "qapi/error.h"

typedef struct AlxState_st {
	PCIDevice parent_obj;
	
	NICState *nic;
	NICConf conf;
	MemoryRegion mmio;
	MemoryRegion io;
    MemoryRegion msix;
} AlxState;

typedef struct AlxClass {
	PCIDeviceClass parent_class;
} AlxClass;

#define ALX(obj) \
	OBJECT_CHECK(AlxState, (obj), TYPE_PCI_DEVICE)

static void alx_class_init(ObjectClass *klass, void *data);
static void pci_alx_realize(PCIDevice *pci_dev, Error **errp);
static void alx_instance_init(Object *obj);
static void alx_register_types(void);

static Property alx_properties[] = {
	DEFINE_NIC_PROPERTIES(AlxState, conf),
	DEFINE_PROP_END_OF_LIST(),
};

static uint64_t alx_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    AlxState *s = opaque;
	printf("mmio_read: %lx %u\n", addr, size);

    (void)s;
    return 0;
}

static void alx_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    AlxState *s = opaque;
	printf("mmio_write: %lx %lx %u\n", addr, val, size);

    (void)s;
}
static const MemoryRegionOps alx_mmio_ops = {
    .read = alx_mmio_read,
    .write = alx_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
	/*
    .impl = {
        .min_access_size = 4,
        .max_access_size = 4,
    },
	*/
};

static uint64_t alx_msix_table_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //AlxState *s = opaque;
	printf("msix_table_mmio_read: %lx %u\n", addr, size);

    return msix_table_mmio_read(opaque, addr, size);
}

static void alx_msix_table_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //AlxState *s = opaque;
	printf("msix_table_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_table_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps alx_msix_table_mmio_ops = {
    .read = alx_msix_table_mmio_read,
    .write = alx_msix_table_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static uint64_t alx_msix_pba_mmio_read(void *opaque, hwaddr addr,
                              unsigned size) {

    //AlxState *s = opaque;
	printf("msix_pba_mmio_read: %lx %u\n", addr, size);

    return msix_pba_mmio_read(opaque, addr, size);
}

static void alx_msix_pba_mmio_write(void *opaque, hwaddr addr,
                           uint64_t val, unsigned size) {
    //AlxState *s = opaque;
	printf("msix_pba_mmio_write: %lx %lx %u\n", addr, val, size);

    msix_pba_mmio_write(opaque, addr, val, size);

}

static const MemoryRegionOps alx_msix_pba_mmio_ops = {
    .read = alx_msix_pba_mmio_read,
    .write = alx_msix_pba_mmio_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static void alx_class_init(ObjectClass *klass, void *data) {
	printf("Entering alx_class_init\n");
	DeviceClass *dc = DEVICE_CLASS(klass);
	PCIDeviceClass *k = PCI_DEVICE_CLASS(klass);

	k->realize = pci_alx_realize;
	k->vendor_id = 0x1969;
	k->device_id = 0x1091;
	k->subsystem_vendor_id = 0x1969;
	k->subsystem_id = 0x0091;
	k->revision = 0;
	k->class_id = PCI_CLASS_NETWORK_ETHERNET;
	set_bit(DEVICE_CATEGORY_NETWORK, dc->categories);

	dc->props = alx_properties;
	printf("Leaving alx_class_init\n");
}

static int alx_add_pm_capability(PCIDevice *pdev) {
	Error *local_err = NULL;
	/* offset 0 to auto mode */
	uint8_t offset = 0;
	 
	int ret = pci_add_capability(pdev, PCI_CAP_ID_PM, offset,
			PCI_PM_SIZEOF, &local_err);
	if (local_err) {
		error_report_err(local_err);
	}
	return ret;
}

static int alx_init_msix(PCIDevice *pdev) {
	AlxState *d = ALX(pdev);
	/* More on magic numbers */
    int res = __msix_init(PCI_DEVICE(d), 5,
                        &d->msix,
                        1, 0x0000, 
                        &d->msix,
                        1, 0x2000,
                        0xA0, NULL,
						&alx_msix_table_mmio_ops,
						&alx_msix_pba_mmio_ops);
	return res;
}

static void pci_alx_realize(PCIDevice *pci_dev, Error **errp) {
	printf("Entering pci_alx_realize\n");
	//DeviceState *dev = DEVICE(pci_dev);
	AlxState *d = ALX(pci_dev);
	qemu_macaddr_default_if_unset(&d->conf.macaddr);

    memory_region_init_io(&d->mmio, OBJECT(d), &alx_mmio_ops, d,
                          "alx-mmio", 0x10000);
    pci_register_bar(pci_dev, 0, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->mmio);

	memory_region_init(&d->msix, OBJECT(d), "alx-msix",
                       0x10000);
    pci_register_bar(pci_dev, 1, PCI_BASE_ADDRESS_SPACE_MEMORY, &d->msix);

	if (alx_add_pm_capability(pci_dev) < 0) {
		hw_error("Failed to initialize PM capability");
	}

	if (alx_init_msix(pci_dev) < 0) {
		hw_error("Failed to initialize MSIX");
	}

	printf("Leaving pci_alx_realize\n");
}

static void alx_instance_init(Object *obj) {
	printf("Entering alx_instance_init\n");
	AlxState *n = ALX(obj);
	device_add_bootindex_property(obj, &n->conf.bootindex,
					"bootindex", "ethernet-phy@0",
					DEVICE(n), NULL);
	printf("Leavin alx_instance_init\n");
}

static const TypeInfo alx_info = {
	.name          = "alx",
	.parent        = TYPE_PCI_DEVICE,
	.instance_size = sizeof(AlxState),
	.instance_init = alx_instance_init,
	.class_size    = sizeof(AlxClass),
	.abstract      = false,
	.class_init    = alx_class_init,
	.instance_init = alx_instance_init,
	.interfaces = (InterfaceInfo[]) {
		{ INTERFACE_CONVENTIONAL_PCI_DEVICE },
		{ },
	},
};

static void alx_register_types(void) {
	printf("Entering alx_register_types\n");
	type_register_static(&alx_info);
	printf("Leaving alx_register_types\n");
}

type_init(alx_register_types)
