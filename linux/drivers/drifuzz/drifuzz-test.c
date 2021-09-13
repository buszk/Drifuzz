#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/ioport.h>       
#include <linux/pci.h>
#include <linux/delay.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Zekun Shen");
MODULE_DESCRIPTION("A command channel between linux guest and qemu host");
MODULE_VERSION("0.01");

#define qemu_driver_name "Drifuzz Unit Tests"


struct qemu_adapter {
	void* hw_addr;
	struct pci_dev *pdev;
};

static struct qemu_adapter *adapter = NULL;

/* Tests */
static uint32_t read_offset(uint32_t offset) {
	if (!adapter) return 0;
	return readl((char*)adapter->hw_addr + offset);
}

static void write_offset(uint32_t offset, uint32_t val) {
	if (!adapter) return;
	writel(val, (char*)adapter->hw_addr + offset);
}

static void goal(void) {
	if (read_offset(0x88) == 0xffff)
		read_offset(0);
}

static void test_longest(void) {
	if (read_offset(0) == 0x1337) {
		if (read_offset(4) == 0xbeef) {
			goal();
		}
	}
}

static void test_branch(void) {
	uint32_t val = read_offset(0);
	uint32_t suport_list[3] = {0x1111, 0x2222, 0x3333};
	uint32_t supported = 0;
	int i;
	for (i = 0; i < 3; i++)
		if (val == suport_list[i])
			supported = 1;
	if (supported)
		goal();
}

static void test_conflict_branches(void) {
	uint32_t val;
	int i;
	for (i = 0; i < 100; i++) {
		val = read_offset(0);
		if (val & 3) break;
	}
	if (val & 1) return;
	if (!(val &2)) return;
	goal();
}

static void test_short_loop(void) {
	int i;
	for (i = 0; i < 100; i++)
		if (read_offset(0) == 0x1111) 
			goal();
}

static void test_long_loop(void) {
	int i;
	for (i = 0; i < 100; i++)
		write_offset(0, i);
		if (read_offset(0) != i) 
			return;
	goal();
}

#define NUM_TESTS		5
static void (*test_table[NUM_TESTS])(void) = {
	test_longest,
	test_branch,
	test_conflict_branches,
	test_short_loop,
	test_long_loop
};


/* PCI */
static int drifuzz_test_probe(struct pci_dev *pdev, const struct pci_device_id *ent) {
	printk(KERN_INFO "Test probe\n");
	int err;
	if ((err = pci_enable_device(pdev)))
		return err;

	adapter = kmalloc(sizeof(struct qemu_adapter), GFP_KERNEL);
	adapter->hw_addr = pci_ioremap_bar(pdev, 0);
	pci_set_drvdata(pdev, adapter);

	if (pdev->revision < NUM_TESTS) {
		printk(KERN_INFO "Running test\n");
		test_table[pdev->revision]();
	}
	return 0;
}

static void drifuzz_test_remove(struct pci_dev *pdev) {
	//pci_release_selected_regions(pdev, bars);
	kfree(pci_get_drvdata(pdev));
	pci_disable_device(pdev);
}

static const struct pci_device_id qemu_pci_tbl[] = {
	{PCI_DEVICE(0x8888, 0)},
	{}
};
static struct pci_driver qemu_driver = {
	.name 		= qemu_driver_name,
	.id_table 	= qemu_pci_tbl,
	.probe 		= drifuzz_test_probe,
	.remove 	= drifuzz_test_remove,
};

/* PCI ends */


int __init qemu_init_module(void) {
	int ret;
	printk(KERN_INFO "Test init\n");
	if ((ret = pci_register_driver(&qemu_driver)) != 0) {
		printk(KERN_ALERT "Could not register pci: %d\b", ret);
		return ret;
	}
	return 0;
}
module_init(qemu_init_module);